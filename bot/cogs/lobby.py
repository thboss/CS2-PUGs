# lobby.py

from asyncpg.exceptions import UniqueViolationError
from typing import List
from collections import defaultdict
import asyncio

from discord.ext import commands
from discord import PermissionOverwrite, app_commands, Interaction, Embed, Member, VoiceState, HTTPException

from bot.bot import G5Bot
from bot.helpers.models import LobbyModel
from bot.helpers.errors import CustomError, JoinLobbyError
from bot.views import ReadyView


CAPACITY_CHOICES = [
    app_commands.Choice(name="1vs1", value=2),
    app_commands.Choice(name="2vs2", value=4),
    app_commands.Choice(name="3vs3", value=6),
    app_commands.Choice(name="4vs4", value=8),
    app_commands.Choice(name="5vs5", value=10),
    app_commands.Choice(name="6vs6", value=12),
]

TEAM_SELECTION_CHOICES = [
    app_commands.Choice(name="Random", value="random"),
    app_commands.Choice(name="Autobalance", value="autobalance"),
    app_commands.Choice(name="Captains", value="captains"),
]

CAPTAIN_SELECTION_CHOICES = [
    app_commands.Choice(name="Random", value="random"),
    app_commands.Choice(name="Rank", value="rank"),
    app_commands.Choice(name="Volunteer", value="volunteer"),
]

MAP_SELECTION_CHOICES = [
    app_commands.Choice(name="Random", value="random"),
    app_commands.Choice(name="Veto", value="veto"),
]

GAME_MODE_CHOICES = [
    app_commands.Choice(name="Competitive", value="competitive"),
    app_commands.Choice(name="Wingman", value="wingman"),
]

CONNECT_TIME_CHOICES = [
    app_commands.Choice(name="1 minute", value=60),
    app_commands.Choice(name="2 minute", value=120),
    app_commands.Choice(name="3 minute", value=180),
    app_commands.Choice(name="5 minute", value=300),
    app_commands.Choice(name="10 minute", value=600)
]


class LobbyCog(commands.Cog, name="Lobby"):
    """A cog for managing lobbies."""

    def __init__(self, bot: G5Bot):
        self.bot = bot
        self.locks = defaultdict(lambda: asyncio.Lock())
        self.in_progress = defaultdict(lambda: False)

    @app_commands.command(
        name='create-lobby',
        description='Create a new lobby.'
    )
    @app_commands.describe(
        capacity="Capacity of the lobby",
        teams_method="Teams selection method",
        captains_method="Captains selection method",
        map_method="Map selection method",
        connect_time="Time in seconds until match is canceled if not everyone has joined",
    )
    @app_commands.choices(
        capacity=CAPACITY_CHOICES,
        teams_method=TEAM_SELECTION_CHOICES,
        captains_method=CAPTAIN_SELECTION_CHOICES,
        map_method=MAP_SELECTION_CHOICES,
        game_mode=GAME_MODE_CHOICES,
        connect_time=CONNECT_TIME_CHOICES,
    )
    @app_commands.checks.has_permissions(administrator=True)
    async def create_lobby(
        self,
        interaction: Interaction,
        capacity: app_commands.Choice[int],
        game_mode: app_commands.Choice[str],
        connect_time: app_commands.Choice[int],
        teams_method: app_commands.Choice[str],
        captains_method: app_commands.Choice[str],
        map_method: app_commands.Choice[str]
    ):
        """ Create a new lobby. """
        await interaction.response.defer(ephemeral=True)

        guild = interaction.guild
        guild_model = await self.bot.db.get_guild_by_id(guild.id)

        perms = {
            guild.self_role: PermissionOverwrite(connect=True, send_messages=True),
            guild.default_role: PermissionOverwrite(connect=False, send_messages=False),
            guild_model.linked_role: PermissionOverwrite(connect=True)
        }
        voice_channel = await guild.create_voice_channel(
            category=guild_model.category,
            name='Lobby',
            user_limit=capacity.value,
            overwrites=perms
        )

        lobby_data = {
            'guild': guild.id,
            'capacity': capacity.value,
            'game_mode': game_mode.value,
            'connect_time': connect_time.value,
            'team_method': teams_method.value,
            'captain_method': captains_method.value,
            'map_method': map_method.value,
            'lobby_channel': voice_channel.id
        }

        lobby_id = await self.bot.db.insert_lobby(lobby_data)

        await voice_channel.edit(name=f"Lobby #{lobby_id}")

        lobby_model = await self.bot.db.get_lobby_by_id(lobby_id)
        await self.update_queue_msg(lobby_model)

        embed = Embed(
            description=f"Lobby #{lobby_id} created successfully.")
        await interaction.followup.send(embed=embed, ephemeral=True)

    @app_commands.command(
        name='delete-lobby',
        description='delete a lobby.'
    )
    @app_commands.describe(lobby_id="Lobby ID.")
    @app_commands.checks.has_permissions(administrator=True)
    async def delete_lobby(self, interaction: Interaction, lobby_id: int):
        """"""
        await interaction.response.defer(ephemeral=True)
        guild = interaction.guild
        lobby_model = await self.bot.db.get_lobby_by_id(lobby_id)
        if not lobby_model:
            raise CustomError("Invalid Lobby ID")

        if lobby_model.guild.id != guild.id:
            raise CustomError("This lobby was not created in this server.")

        try:
            await self.bot.db.delete_lobby(lobby_id)
        except Exception as e:
            self.bot.log_exception(f"Failed to remove lobby #{lobby_id}:", e)
            raise CustomError("Something went wrong! Please try again later.")

        try:
            await lobby_model.voice_channel.delete()
        except HTTPException:
            pass

        embed = Embed(description=f"Lobby #{lobby_model.id} has been removed.")
        await interaction.followup.send(embed=embed, ephemeral=True)

    @app_commands.command(
        name='empty-lobby',
        description='Empty a lobby and move users into Waiting Room.'
    )
    @app_commands.describe(lobby_id="Lobby ID.")
    @app_commands.checks.has_permissions(administrator=True)
    async def empty_lobby(self, interaction: Interaction, lobby_id: int):
        """"""
        await interaction.response.defer(ephemeral=True)
        guild = interaction.guild
        lobby_model = await self.bot.db.get_lobby_by_id(lobby_id)
        guild_model = await self.bot.db.get_guild_by_id(guild.id)
        if not lobby_model:
            raise CustomError("Invalid Lobby ID")

        if lobby_model.guild.id != guild.id:
            raise CustomError("This lobby was not created in this server.")

        async with self.locks[lobby_model.id]:
            for user in lobby_model.voice_channel.members:
                try:
                    await user.move_to(guild_model.waiting_channel)
                except Exception as e:
                    pass

            await self.bot.db.clear_lobby_users(lobby_model.id)
            await self.update_queue_msg(lobby_model, title="Lobby has been emptied")

        embed = Embed(description=f"Lobby #{lobby_model.id} has been emptied.")
        await interaction.followup.send(embed=embed, ephemeral=True)

    @app_commands.command(name="add-spectator", description="Add a user to the spectators list")
    @app_commands.checks.has_permissions(administrator=True)
    async def add_spectator(self, interaction: Interaction, user: Member):
        """"""
        await interaction.response.defer()
        player_model = await self.bot.db.get_player_by_discord_id(user.id)
        if not player_model:
            raise CustomError(f"User {user.mention} must be linked.")
        
        try:
            await self.bot.db.insert_spectators(user, guild=interaction.guild)
        except UniqueViolationError:
            raise CustomError(f"User {user.mention} is already in spectators list")

        embed = Embed(description=f"User {user.mention} has successfully added to the spectators list")
        await interaction.followup.send(embed=embed)

    @app_commands.command(name="remove-spectator", description="Remove a user from the spectators list")
    @app_commands.checks.has_permissions(administrator=True)
    async def remove_spectator(self, interaction: Interaction, user: Member):
        """"""
        await interaction.response.defer()
        deleted = await self.bot.db.delete_spectators(user, guild=interaction.guild)
        if not deleted:
            raise CustomError(f"User {user.mention} is not in spectators list")
        
        embed = Embed(description=f"User {user.mention} has successfully removed from spectators list")
        await interaction.followup.send(embed=embed)

    @app_commands.command(name="spectators-list", description="Show list of match spectators")
    async def spectators_list(self, interaction: Interaction):
        """"""
        await interaction.response.defer()
        spectators = await self.bot.db.get_spectators(interaction.guild)
        
        if spectators:
            description = "\n".join(f"{idx}. {spec.user.mention}" for idx, spec in enumerate(spectators))
        else:
            description = "No spectators found"

        embed = Embed(description=description)
        await interaction.followup.send(embed=embed)
        
    @commands.Cog.listener()
    async def on_voice_state_update(self, user: Member, before: VoiceState, after: VoiceState):
        """"""
        if before.channel == after.channel:
            return

        if before.channel is not None:
            lobby_model = await self.bot.db.get_lobby_by_channel(before.channel)
            if lobby_model:
                if not self.in_progress[lobby_model.id]:
                    async with self.locks[lobby_model.id]:
                        try:
                            await self._leave(user, lobby_model)
                        except Exception as e:
                            self.bot.log_exception(
                                "Uncaght exception when handling 'cogs.lobby._leave()' method:", e)

        if after.channel is not None:
            lobby_model = await self.bot.db.get_lobby_by_channel(after.channel)
            if lobby_model:
                if not self.in_progress[lobby_model.id]:
                    async with self.locks[lobby_model.id]:
                        try:
                            await self._join(user, lobby_model)
                        except Exception as e:
                            self.bot.logger.error(
                                "Uncaught exception when handling 'cogs.lobby._join()' method:", e, exc_info=1)

    async def _leave(self, user: Member, lobby_model: LobbyModel):
        """"""
        removed = await self.bot.db.delete_lobby_users(lobby_model.id, [user])
        if removed:
            title = f"User {user.display_name} removed from the lobby"
            await self.update_queue_msg(lobby_model, title)

    async def _join(self, user: Member, lobby_model: LobbyModel):
        """"""
        lobby_users = await self.bot.db.get_lobby_users(lobby_model.id, lobby_model.guild)
        try:
            await self.add_user_to_lobby(user, lobby_model, lobby_users)
        except JoinLobbyError as e:
            title = e.message
        else:
            title = f"User **{user.display_name}** added to the queue."
            lobby_users.append(user)

            if len(lobby_users) == lobby_model.capacity:
                self.in_progress[lobby_model.id] = True
                title = None
                guild_model = await self.bot.db.get_guild_by_id(lobby_model.guild.id)
                lobby_model = await self.bot.db.get_lobby_by_id(lobby_model.id)

                try:
                    queue_msg = await lobby_model.voice_channel.fetch_message(lobby_model.message_id)
                    await queue_msg.delete()
                except:
                    pass

                unreadied_users = []
                ready_view = ReadyView(lobby_users, lobby_model.voice_channel)
                await ready_view.start()
                await ready_view.wait()
                unreadied_users = set(lobby_users) - ready_view.ready_users

                if unreadied_users:
                    awaitables = [u.move_to(guild_model.waiting_channel) for u in unreadied_users]
                    awaitables.append(self.bot.db.delete_lobby_users(lobby_model.id, unreadied_users))
                    await asyncio.gather(*awaitables, return_exceptions=True)
                else:
                    embed = Embed(description='Starting match setup...')
                    setup_msg = await lobby_model.voice_channel.send(embed=embed)

                    match_cog = self.bot.get_cog('Match')
                    match_started = await match_cog.start_match(
                        lobby_model.guild,
                        setup_msg,
                        lobby_model.voice_channel,
                        queue_users=lobby_users,
                        team_method=lobby_model.team_method,
                        captain_method=lobby_model.captain_method,
                        map_method=lobby_model.map_method,
                        game_mode=lobby_model.game_mode,
                        connect_time=lobby_model.connect_time
                    )
                    if not match_started:
                        awaitables = [u.move_to(guild_model.waiting_channel) for u in lobby_users]
                        await asyncio.gather(*awaitables, return_exceptions=True)

                    await self.bot.db.clear_lobby_users(lobby_model.id)
                self.in_progress[lobby_model.id] = False

        await self.update_queue_msg(lobby_model, title)

    async def add_user_to_lobby(self, user: Member, lobby_model: LobbyModel, lobby_users: List[Member]):
        """"""
        player_model = await self.bot.db.get_player_by_discord_id(user.id)
        match_data = await self.bot.db.get_user_match(user.id, lobby_model.guild)

        if not player_model:
            raise JoinLobbyError(user, "User not linked")
        if match_data:
            raise JoinLobbyError(user, "User in match")
        if user in lobby_users:
            raise JoinLobbyError(user, "User in lobby")
        if len(lobby_users) >= lobby_model.capacity:
            raise JoinLobbyError(user, "Lobby is full")
        try:
            await self.bot.db.insert_lobby_user(lobby_model.id, user)
        except UniqueViolationError:
            raise JoinLobbyError(user, "Please try again (Database Error)")

    async def update_queue_msg(self, lobby_model: LobbyModel, title: str=None):
        """"""
        if not lobby_model.voice_channel:
            return

        lobby_model = await self.bot.db.get_lobby_by_id(lobby_model.id)
        lobby_users = await self.bot.db.get_lobby_users(lobby_model.id, lobby_model.guild)

        try:
            queue_message = await lobby_model.voice_channel.fetch_message(lobby_model.message_id)
        except:
            queue_message = await lobby_model.voice_channel.send(embed=Embed(description="New Queue Message"))
            await self.bot.db.update_lobby(lobby_model.id, {'last_message': queue_message.id})

        embed = self._embed_queue(
            title, lobby_model, lobby_users)
        await queue_message.edit(embed=embed, view=None)

    def _embed_queue(self, title: str, lobby_model: LobbyModel, lobby_users: List[Member]):
        """"""
        embed = Embed(title=title)

        info_str = f"Game mode: *{lobby_model.game_mode.capitalize()}*\n" \
                   f"Teams selection: *{lobby_model.team_method.capitalize()}*\n" \
                   f"Captains selection: *{lobby_model.captain_method.capitalize()}*\n" \
                   f"Maps selection: *{lobby_model.map_method.capitalize()}*"

        queued_players_str = "*Lobby is empty*" if not lobby_users else ""
        for num, user in enumerate(lobby_users, start=1):
            queued_players_str += f'{num}. {user.mention}\n'

        embed.add_field(name="**__Settings__**", value=info_str, inline=False)
        embed.add_field(
            name=f"**__Players__** `({len(lobby_users)}/{lobby_model.capacity})`:",
            value=queued_players_str
        )
        embed.set_author(name=f"Lobby #{lobby_model.id}")
        if self.bot.user.avatar:
            embed.set_thumbnail(url=self.bot.user.avatar.url)
        return embed


async def setup(bot: G5Bot):
    await bot.add_cog(LobbyCog(bot))
