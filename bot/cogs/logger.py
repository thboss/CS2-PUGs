# logger.py

import __main__
import logging
from logging import config
import platform
import os
import traceback

import discord
from discord.ext import commands

from bot.helpers.utils import indent
from bot.resources import Config


class ConsoleFormatter(logging.Formatter):
    """"""

    def __init__(self, fmt=None, datefmt=None):
        super().__init__(fmt=fmt, datefmt=datefmt)

    # Colors
    black = "\x1b[30m"
    red = "\x1b[31m"
    green = "\x1b[32m"
    yellow = "\x1b[33m"
    blue = "\x1b[34m"
    gray = "\x1b[38m"
    # Styles
    reset = "\x1b[0m"
    bold = "\x1b[1m"

    COLORS = {
        logging.DEBUG: gray + bold,
        logging.INFO: blue + bold,
        logging.WARNING: yellow + bold,
        logging.ERROR: red,
        logging.CRITICAL: red + bold,
    }

    def format(self, record):
        log_color = self.COLORS[record.levelno]
        format = "(gray)[{asctime}](green)[{name}](levelcolor)[{levelname}] (reset){message}"
        format = format.replace("(gray)", self.gray + self.bold)
        format = format.replace("(reset)", self.reset)
        format = format.replace("(levelcolor)", log_color)
        format = format.replace("(green)", self.green + self.bold)
        formatter = logging.Formatter(format, "%H:%M:%S", style="{")
        return formatter.format(record)


LOGGING_CONFIG = {
    'version': 1,
    'formatters': {
        'default': {
            'format': '[%(asctime)s][%(name)s][%(levelname)s] %(message)s',
            'datefmt': '%Y-%m-%d %H:%M:%S'
        },
        'color': {
            '()': ConsoleFormatter,
            'format': '[%(asctime)s][%(name)s][%(levelname)s] %(message)s',
            'datefmt': '%H:%M:%S'
        }
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'color',
            'level': 'DEBUG',
            'stream': 'ext://sys.stdout'
        },
        'file': {
            'class': 'logging.handlers.RotatingFileHandler',
            'formatter': 'default',
            'level': 'DEBUG',
            'filename': os.path.join(os.path.dirname(os.path.abspath(__main__.__file__)), 'bot.log'),
            'maxBytes': 7340032,
            'encoding': 'utf-8'
        }
    },
    'loggers': {
        'Bot': {
            'level': 'DEBUG' if Config.debug else 'INFO',
        },
        'API': {
            'level': 'DEBUG' if Config.debug else 'INFO',
        },
        'DB': {
            'level': 'DEBUG' if Config.debug else 'INFO',
        },
        'discord': {
            'level': 'INFO',
        }
    },
    'root': {
        'level': 'DEBUG',
        'handlers': [
            'console',
            'file'
        ]
    }
}

config.dictConfig(LOGGING_CONFIG)


def log_lines(lvl, msg, *args, sub_lines=None, **kwargs):
    """"""
    if sub_lines is not None:
        longest_subl_pref = len(max(sub_lines.keys(), key=len))

        for prefix, suffix in sub_lines.items():
            msg += '\n    {:<{width}} {}'.format(
                prefix + ':', suffix, width=longest_subl_pref + 1)

    logging.getLogger('Bot').log(lvl, msg, *args, **kwargs)


class Logger(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.logger = logging.getLogger("Bot")

    def log_exception(self, msg, error):
        """"""
        msg += '\n\n'
        exc_lines = traceback.format_exception(
            type(error), error, error.__traceback__)
        exc = ''.join(exc_lines)
        self.logger.error(msg + indent(exc))

    @commands.Cog.listener()
    async def on_connect(self):
        lines_dict = {'Username': self.bot.user.name, 'ID': self.bot.user.id}
        log_lines(logging.INFO, 'Connected to Discord', sub_lines=lines_dict)

    @commands.Cog.listener()
    async def on_disconnect(self):
        log_lines(logging.INFO, 'Disconnected from Discord')

    @commands.Cog.listener()
    async def on_resumed(self):
        lines_dict = {'Username': self.bot.user.name, 'ID': self.bot.user.id}
        log_lines(logging.INFO, 'Resumed session with Discord',
                  sub_lines=lines_dict)

    @commands.Cog.listener()
    async def on_ready(self):
        log_lines(logging.INFO, f"Logged in as {self.bot.user.name}")
        log_lines(logging.INFO,
                  f"discord.py API version: {discord.__version__}")
        log_lines(logging.INFO, f"Python version: {platform.python_version()}")
        log_lines(
            logging.INFO,
            f"Running on: {platform.system()} {platform.release()} ({os.name})")

    @commands.Cog.listener()
    async def on_guild_join(self, guild):
        log_lines(
            logging.INFO,
            'Bot has been added to server "%s" (%s)', guild.name, guild.id)

    @commands.Cog.listener()
    async def on_guild_remove(self, guild):
        log_lines(
            logging.INFO,
            'Bot has been removed from server "%s" (%s)', guild.name, guild.id)

    @commands.Cog.listener()
    async def on_app_command_completion(self, interaction: discord.Interaction, command: discord.app_commands.Command) -> None:
        """ Executed when a normal command has been successfully executed. """
        user = interaction.user
        guild = interaction.guild
        lines_dict = {
            'User': f'{user} ({user.id if user else None})',
            'Guild': f'{guild} ({guild.id if guild else None})'
        }
        log_lines(logging.INFO, 'Command "%s" issued',
                  command.name, sub_lines=lines_dict)


async def setup(bot):
    await bot.add_cog(Logger(bot))
