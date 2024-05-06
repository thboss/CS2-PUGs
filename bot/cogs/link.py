# link.py

from asyncpg.exceptions import UniqueViolationError

from discord.ext import commands
from discord import app_commands, Embed, Interaction
from bot.helpers.errors import CustomError
from bot.helpers.utils import validate_steam
from bot.bot import G5Bot


class LinkCog(commands.Cog, name='Link'):
    def __init__(self, bot: G5Bot):
        self.bot = bot

    @app_commands.command(name='link-steam', description='Link your Discord account to Steam.')
    @app_commands.describe(steam='Steam ID or Steam profle link')
    async def link_steam(self, interaction: Interaction, steam: str):
        await interaction.response.defer(ephemeral=True)
        user = interaction.user
        steam_id = validate_steam(steam)
        guild_model = await self.bot.db.get_guild_by_id(interaction.guild_id)
        player_model = await self.bot.db.get_player_by_discord_id(user.id)

        if player_model:
            user_match = await self.bot.db.get_user_match(user.id, interaction.guild)
            if user_match:
                raise CustomError(
                    f"You can't change your steam while you belong to a live match #{user_match.id}")
            
            spectators = await self.bot.db.get_spectators(interaction.guild)
            for spec in spectators:
                if spec.user == user:
                    raise CustomError(
                        "You can't change your steam while you are in spectators list.")

        try:
            if not player_model:
                await self.bot.db.insert_player(user.id, int(steam_id))
            else:
                await self.bot.db.update_player(user.id, int(steam_id))
        except UniqueViolationError:
            raise CustomError(
                f"This Steam is linked to another user. Please try different Steam ID.")
        except Exception as e:
            self.bot.logger.error(e, exc_info=1)
            raise CustomError("Something went wrong! Please try again later.")

        await user.add_roles(guild_model.linked_role)

        embed = Embed(
            description=f"You have successfully linked to [Steam](https://steamcommunity.com/profiles/{steam_id}/)")
        await interaction.followup.send(embed=embed, ephemeral=True)


async def setup(bot):
    await bot.add_cog(LinkCog(bot))
