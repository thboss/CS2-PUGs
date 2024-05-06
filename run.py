# bot.py

import asyncio
import os
import json

from discord import Intents

from bot.resources import Config
from bot.bot import G5Bot


_CWD = os.path.dirname(os.path.abspath(__file__))
INTENTS_FILE = os.path.join(_CWD, 'intents.json')
with open(INTENTS_FILE) as f:
    intents_json = json.load(f)


intents = Intents(**intents_json)
bot = G5Bot(intents=intents)


async def main():
    await bot.load_cogs()
    await bot.start(Config.token)


asyncio.run(main())
