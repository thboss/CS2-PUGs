# bot.py

import logging
import os
import traceback

from discord.ext import commands
from discord import Guild

from .helpers.webhook import WebServer

from .helpers.db import DBManager
from .helpers.api import APIManager
from .helpers.errors import on_app_command_error


class G5Bot(commands.AutoShardedBot):
    """ A Discord bot class with sharding capabilities. """

    def __init__(self, intents: dict) -> None:
        super().__init__(command_prefix=commands.when_mentioned_or('!'), help_command=None, intents=intents)

        self.description = ""
        self.logger = logging.getLogger('Bot')
        self.tree.on_error = on_app_command_error
        self.db: DBManager = DBManager(self)
        self.api: APIManager = APIManager(self)
        self.webserver: WebServer = None

    @commands.Cog.listener()
    async def on_ready(self) -> None:
        await self.db.connect()
        self.api.connect(self.loop)
        self.webserver = WebServer(self)
        await self.webserver.start_webhook_server()

        #  Sync guilds' information with the database.
        if self.guilds:
            await self.db.sync_guilds([g.id for g in self.guilds])
            for guild in self.guilds:
                try:
                    await self.check_guild_requirements(guild)
                except: pass

        self.logger.info("Syncing commands globally...")
        await self.tree.sync()
        self.logger.info("Commands have been successfully synced globally.")
        self.logger.info('Bot is ready to use in %s Discord servers', len(self.guilds))

    @commands.Cog.listener()
    async def on_guild_join(self, guild) -> None:
        """"""
        await self.db.sync_guilds([g.id for g in self.guilds])
        try:
            await self.check_guild_requirements(guild)
        except: pass

    @commands.Cog.listener()
    async def on_guild_remove(self, guild) -> None:
        """"""
        await self.db.sync_guilds([g.id for g in self.guilds])

    async def close(self):
        """"""
        await super().close()
        await self.db.close()
        await self.api.close()

    async def load_cogs(self) -> None:
        """ Load extensions in the cogs folder. """
        _CWD = os.path.dirname(os.path.abspath(__file__))
        cogs = os.listdir(_CWD + "/cogs")
        # Ensure the logger cog is loaded first.
        cogs.insert(0, cogs.pop(cogs.index('logger.py')))
        for file in cogs:
            if file.endswith(".py"):
                extension = file[:-3]
                try:
                    await self.load_extension(f"bot.cogs.{extension}")
                    self.logger.info(f"Loaded extension '{extension}'")
                except Exception as e:
                    traceback.print_exc()
                    exception = f"{type(e).__name__}: {e}"
                    self.logger.error(
                        f"Failed to load extension {extension}\n{exception}")

    async def check_guild_requirements(self, guild: Guild) -> None:
        """
        Check and set up the required channels, roles, and category for the guild.
        """
        guild_model = await self.db.get_guild_by_id(guild.id)
        category = guild_model.category
        linked_role = guild_model.linked_role
        waiting_channel = guild_model.waiting_channel
        results_channel = guild_model.results_channel
        leaderboard_channel = guild_model.leaderboard_channel

        if any(x is None for x in [category, linked_role, waiting_channel, results_channel, leaderboard_channel]):
            if not category:
                category = await guild.create_category_channel('G5')
            if not linked_role:
                linked_role = await guild.create_role(name='Linked')
            if not waiting_channel:
                waiting_channel = await category.create_voice_channel(name='Waiting Room')
            if not results_channel:
                results_channel = await category.create_text_channel(name='Results')
                await results_channel.set_permissions(guild.self_role, send_messages=True)
                await results_channel.set_permissions(guild.default_role, send_messages=False)
            if not leaderboard_channel:
                leaderboard_channel = await category.create_text_channel(name='Leaderboard')
                await leaderboard_channel.set_permissions(guild.self_role, send_messages=True)
                await leaderboard_channel.set_permissions(guild.default_role, send_messages=False)

            dict_data = {
                'category': category.id,
                'linked_role': linked_role.id,
                'waiting_channel': waiting_channel.id,
                'results_channel': results_channel.id,
                'leaderboard_channel': leaderboard_channel.id,
            }
            await self.db.update_guild_data(guild.id, dict_data)
