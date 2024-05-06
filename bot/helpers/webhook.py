import logging
from aiohttp import web

from bot.helpers.api import Match
from bot.resources import Config
from bot.helpers.utils import generate_leaderboard_img, generate_scoreboard_img


class WebServer:
    _instance = None  # Class variable to store the single instance

    def __new__(cls, bot):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self, bot):
        if getattr(self, 'initialized', False):
            return
        self.initialized = True  # Ensure initialization only once
        self.server_running = False
        self.bot = bot
        self.logger = logging.getLogger("API")
        self.host = Config.webserver_host
        self.port = Config.webserver_port
        self.match_cog = self.bot.get_cog("Match")

    async def match_end(self, req):
        self.logger.info(f"Received webhook data from {req.url}")
        api_key = req.headers.get('Authorization').strip('Bearer ')
        match_model = await self.bot.db.get_match_by_api_key(api_key)
        resp_data = await req.json()
        match_api = Match.from_dict(resp_data)
        if not match_model or not match_api:
            return

        try:
            await self.bot.api.stop_game_server(match_model.game_server_id)
        except Exception as e:
            self.logger.error(e, exc_info=1)

        guild_model = await self.bot.db.get_guild_by_id(match_model.guild.id)
        match_api = await self.bot.api.get_match(match_model.id)
        await self.match_cog.finalize_match(match_model, match_api, guild_model)

    async def round_end(self, req):
        self.logger.debug(f"Received webhook data from {req.url}")
        game_server = None
        message = None
        api_key = req.headers.get('Authorization').strip('Bearer ')
        match_model = await self.bot.db.get_match_by_api_key(api_key)
        resp_data = await req.json()
        match_api = Match.from_dict(resp_data)
        # guild_model = await self.bot.db.get_guild_by_id(match_model.guild.id)
        if not match_model or not match_api:
            return

        for player_stat in match_api.players:
            try:
                player_model = await self.bot.db.get_player_by_steam_id(player_stat.steam_id)
                if player_model:
                    await self.bot.db.update_player_stats(player_model.discord.id, match_api.id, player_stat.to_dict)
            except Exception as e:
                self.logger.error(e, exc_info=1)

        try:
            message = await match_model.text_channel.fetch_message(match_model.message_id)
        except Exception as e:
            self.logger.error(e, exc_info=1)

        try:
            game_server = await self.bot.api.get_game_server(match_api.game_server_id)
        except Exception as e:
            self.logger.error(e, exc_info=1)

        if message:
            try:
                embed = self.match_cog.embed_match_info(match_api, game_server)
                await message.edit(embed=embed)
            except Exception as e:
                self.logger.error(e, exc_info=1)

    async def start_webhook_server(self):
        if self.server_running:
            self.logger.warning("Webhook server is already running.")
            return

        self.logger.info(f'Starting webhook server on {self.host}:{self.port}')

        app = web.Application()

        app.router.add_post("/cs2bot-api/match-end", self.match_end)
        app.router.add_post("/cs2bot-api/round-end", self.round_end)

        runner = web.AppRunner(app)
        await runner.setup()

        site = web.TCPSite(runner, host=self.host, port=self.port)

        try:
            await site.start()
            self.server_running = True
            self.logger.info("Webhook server started and running in the background")
        except Exception as e:
            self.logger.error("Failed to start the webhook server.", e, exc_info=1)
            self.server_running = False
