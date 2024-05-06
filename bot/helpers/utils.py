import secrets
import string
from steam import steamid
from PIL import Image, ImageFont, ImageDraw
from discord import File, Embed, Member
import os

from bot.helpers.models.playerstats import PlayerStatsModel

from .errors import CustomError


ABS_ROOT_DIR = os.path.abspath(os.curdir)
TEMPLATES_DIR = os.path.join(ABS_ROOT_DIR, 'assets', 'img', 'templates')
FONTS_DIR = os.path.join(ABS_ROOT_DIR, 'assets', 'fonts')
SAVE_IMG_DIR = os.path.join(ABS_ROOT_DIR, 'assets', 'img')


GAME_SERVER_LOCATIONS = {
    "beauharnois": "Canada",
    "new_york_city": "USA - NY",
    "los_angeles": "USA - CA",
    "miami": "USA - FL",
    "chicago": "USA - IL",
    "portland": "USA - WA",
    "dallas": "USA - TX",
    "copenhagen": "Denmark",
    "helsinki": "Finland",
    "strasbourg": "France",
    "dusseldorf": "Germany",
    "amsterdam": "Netherlands",
    "warsaw": "Poland",
    # "moscow": "Russia",
    "barcelona": "Spain",
    "stockholm": "Sweden",
    "istanbul": "Turkey",
    "bristol": "United Kingdom",
    "sydney": "Australia",
    "sao_paulo": "Brazil",
    "hong_kong": "Hong Kong",
    "mumbai": "India",
    "tokyo": "Japan",
    "singapore": "Singapore",
    "johannesburg": "South Africa"
}


def validate_steam(steam: str) -> int:
    try:
        steam_id = steamid.SteamID(steam)
    except:
        raise CustomError("Invalid Steam!")

    if not steam_id.is_valid():
        steam_id = steamid.from_url(steam, http_timeout=15)
        if steam_id is None:
            steam_id = steamid.from_url(
                f'https://steamcommunity.com/id/{steam}/', http_timeout=15)
            if steam_id is None:
                raise CustomError("Invalid Steam!")

    return steam_id.as_64


def indent(string, n=4):
    """"""
    indent = ' ' * n
    return indent + string.replace('\n', '\n' + indent)


def generate_api_key(length=32):
    alphabet = string.ascii_letters + string.digits
    api_key = ''.join(secrets.choice(alphabet) for _ in range(length))
    return api_key.upper()


def generate_statistics_img(user: Member, stats: PlayerStatsModel):
    """"""
    width, height = 543, 745
    with Image.open(TEMPLATES_DIR + "/statistics.png") as img:
        font = ImageFont.truetype(FONTS_DIR + "/ARIALUNI.TTF", 25)
        draw = ImageDraw.Draw(img)
        fontbig = ImageFont.truetype(FONTS_DIR + "/ARIALUNI.TTF", 36)

        name = user.display_name[:20]
        name_box = draw.textbbox((0, 0), name, font=fontbig)
        name_width = name_box[2] - name_box[0]

        draw.text(((width - name_width) // 2, 32), name, font=fontbig)
        draw.text((65, 226+109*0), str(stats.kills), font=font)
        draw.text((65, 226+109*1), str(stats.deaths), font=font)
        draw.text((65, 226+109*2), str(stats.assists), font=font)
        draw.text((65, 226+109*3), str(stats.headshots), font=font)
        draw.text((65, 226+109*4), str(stats.hsp), font=font)
        draw.text((372, 226+109*0), str(stats.kdr), font=font)
        draw.text((372, 226+109*1), str(stats.total_matches), font=font)
        draw.text((372, 226+109*2), str(stats.wins), font=font)
        draw.text((372, 226+109*3), str(round(stats.win_rate * 100, 2)), font=font)
        draw.text((372, 226+109*4), str(stats.rating), font=font)

        img.save(SAVE_IMG_DIR + '/statistics.png')

    return File(SAVE_IMG_DIR + '/statistics.png', filename="statistics.png")


def generate_leaderboard_img(players_stats):
    """"""
    width, height = 1096, 895

    with Image.open(TEMPLATES_DIR + "/leaderboard.png") as img:
        font = ImageFont.truetype(FONTS_DIR + "/ARIALUNI.TTF", 25)
        draw = ImageDraw.Draw(img)

        for idx, p in enumerate(players_stats):
            draw.text((73, 235+65*idx), str(p.member.display_name)[:14], font=font)
            draw.text((340, 235+65*idx), str(p.kills), font=font)
            draw.text((500, 235+65*idx), str(p.deaths), font=font)
            draw.text((660, 235+65*idx), str(p.played_matches), font=font)
            draw.text((820, 235+65*idx), str(p.wins), font=font)
            draw.text((980, 235+65*idx), str(p.elo), font=font)

        img.save(SAVE_IMG_DIR + '/leaderboard.png')

    return File(SAVE_IMG_DIR + '/leaderboard.png', filename='leaderboard.png')


def generate_scoreboard_img(match_stats, team1_stats, team2_stats):
    """"""
    width, height = 992, 1065

    with Image.open(TEMPLATES_DIR + "/scoreboard.png") as img:
        font = ImageFont.truetype(FONTS_DIR + "/ARIALUNI.TTF", 25)
        fontbig = ImageFont.truetype(FONTS_DIR + "/ARIALUNI.TTF", 32)
        draw = ImageDraw.Draw(img)

        title = f'{match_stats.team1_name[:20]}     {match_stats.team1_score}  :  {match_stats.team2_score}     {match_stats.team2_name[:20]}'
        title_box = draw.textbbox((0, 0), title, font=fontbig)
        title_width = title_box[2] - title_box[0]
        draw.text(((width - title_width) // 2, 40), title, font=fontbig)

        map_name = f"Map: {match_stats.map_name}"
        map_box = draw.textbbox((0, 0), map_name, font=fontbig)
        map_width = map_box[2] - map_box[0]
        draw.text(((width - map_width) // 2, 85), map_name, font=fontbig)

        draw.text((200, 170), match_stats.team1_name[:20], font=fontbig)
        for idx, p in enumerate(team1_stats):
            draw.text((58, 290+50*idx), str(p.discord.display_name)[:14], font=font)
            draw.text((340, 290+50*idx), str(team1_stats[p].kills), font=font)
            draw.text((490, 290+50*idx), str(team1_stats[p].assists), font=font)
            draw.text((640, 290+50*idx), str(team1_stats[p].deaths), font=font)
            draw.text((790, 290+50*idx), str(team1_stats[p].mvps), font=font)
            draw.text((900, 290+50*idx), str(team1_stats[p].score), font=font)
    
        draw.text((200, 615), match_stats.team2_name[:20], font=fontbig)
        for idx, p in enumerate(team2_stats):
            draw.text((58, 748+50*idx), str(p.discord.display_name)[:14], font=font)
            draw.text((340, 748+50*idx), str(team2_stats[p].kills), font=font)
            draw.text((490, 748+50*idx), str(team2_stats[p].assists), font=font)
            draw.text((640, 748+50*idx), str(team2_stats[p].deaths), font=font)
            draw.text((790, 748+50*idx), str(team2_stats[p].mvps), font=font)
            draw.text((900, 748+50*idx), str(team2_stats[p].score), font=font)

        img.save(SAVE_IMG_DIR + '/scoreboard.png')

    return File(SAVE_IMG_DIR + '/scoreboard.png', filename="scoreboard.png")
