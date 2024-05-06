# bot/helpers/models/match.py

import discord
from typing import Optional


class MatchModel:
    """"""

    def __init__(
        self,
        match_id: int,
        guild: Optional[discord.Guild],
        text_channel: Optional[discord.TextChannel],
        message_id: int,
        category: Optional[discord.CategoryChannel],
        team1_channel: Optional[discord.VoiceChannel],
        team2_channel: Optional[discord.VoiceChannel],
        game_server_id: str,
        team1_name: str,
        team2_name: str,
        map_name: str,
        rounds_played: int,
        team1_score: int,
        team2_score: int,
        connect_time: int,
        canceled: bool,
        finished: bool,
        api_key: str
    ):
        """"""
        self.id = match_id
        self.guild = guild
        self.text_channel = text_channel
        self.message_id = message_id
        self.category = category
        self.team1_channel = team1_channel
        self.team2_channel = team2_channel
        self.game_server_id = game_server_id
        self.team1_name = team1_name
        self.team2_name = team2_name
        self.map_name = map_name
        self.rounds_played = rounds_played
        self.team1_score = team1_score
        self.team2_score = team2_score
        self.connect_time = connect_time
        self.canceled = canceled
        self.finished = finished
        self.api_key = api_key

    @classmethod
    def from_dict(cls, data: dict, guild: discord.Guild) -> "MatchModel":
        """"""
        return cls(
            data['id'],
            guild,
            guild.get_channel(data['channel']),
            data['message'],
            guild.get_channel(data['category']),
            guild.get_channel(data['team1_channel']),
            guild.get_channel(data['team2_channel']),
            data['game_server_id'],
            data['team1_name'],
            data['team2_name'],
            data['map_name'],
            data['rounds_played'],
            data['team1_score'],
            data['team2_score'],
            data['connect_time'],
            data['canceled'],
            data['finished'],
            data['api_key']
        )