# bot/helpers/models/playerstats.py


class PlayerStatsModel:
    """"""

    def __init__(
        self,
        user_id: int,
        steam_id: int=None,
        kills: int=0,
        deaths: int=0,
        assists: int=0,
        mvps: int=0,
        headshots: int=0,
        k2: int=0,
        k3: int=0,
        k4: int=0,
        k5: int=0,
        rounds_played: int=0,
        wins: int=0,
        total_matches: int=0
    ):
        """"""
        self.user_id = user_id
        self.steam_id = steam_id
        self.kills = kills
        self.deaths = deaths
        self.assists = assists
        self.mvps = mvps
        self.headshots = headshots
        self.k2 = k2
        self.k3 = k3
        self.k4 = k4
        self.k5 = k5
        self.rounds_played = rounds_played
        self.wins = wins
        self.total_matches = total_matches

    @property
    def kdr(self) -> float:
        return round(self.kills / self.deaths, 2) if self.deaths else 0.00
    
    @property
    def hsp(self) -> float:
        return round(self.headshots / self.kills, 2) * 100 if self.kills else 0.00
    
    @property
    def win_rate(self) -> float:
        return round(self.wins / self.total_matches, 2) if self.total_matches else 0.00
    
    @property
    def assist_rate(self) -> float:
        return round(self.assists / self.rounds_played, 2) if self.rounds_played else 0.00
    
    @property
    def mvp_rate(self) -> float:
        return round(self.mvps / self.rounds_played, 2) if self.rounds_played else 0.00
    
    @property
    def k2_rate(self) -> float:
        return round(self.k2 / self.rounds_played, 2) if self.rounds_played else 0.00
    
    @property
    def k3_rate(self) -> float:
        return round(self.k3 / self.rounds_played, 2) if self.rounds_played else 0.00
    
    @property
    def k4_rate(self) -> float:
        return round(self.k4 / self.rounds_played, 2) if self.rounds_played else 0.00
    
    @property
    def k5_rate(self) -> float:
        return round(self.k5 / self.rounds_played, 2) if self.rounds_played else 0.00
    
    @property
    def rating(self) -> float:
        """
        Calculates the average rating of the player based on provided weights.
        """

        weights = {
            'kdr': 1.0,
            'assist_rate': 0.7,
            'hs_rate': 0.2,
            'mvp_rate': 0.4,
            'k2_rate': 0.6,
            'k3_rate': 3.0,
            'k4_rate': 5.0,
            'k5_rate': 10.0,
            'win_rate': 1.5
        }

        # Calculate weighted sum of relevant stats
        weighted_sum = (
            self.kdr * weights['kdr'] +
            self.assist_rate * weights['assist_rate'] +
            (self.hsp / 100) * weights['hs_rate'] +
            self.mvp_rate * weights['mvp_rate'] +
            self.k2_rate * weights['k2_rate'] +
            self.k3_rate * weights['k3_rate'] +
            self.k4_rate * weights['k4_rate'] +
            self.k5_rate * weights['k5_rate'] +
            self.win_rate * weights['win_rate']
        )

        return round(weighted_sum / 2, 2)

    @classmethod
    def from_dict(cls, data: dict) -> "PlayerStatsModel":
        """"""
        return cls(
            data['user_id'],
            data['steam_id'],
            data['kills'],
            data['deaths'],
            data['assists'],
            data['mvps'],
            data['headshots'],
            data['k2'],
            data['k3'],
            data['k4'],
            data['k5'],
            data['rounds_played'],
            data['wins'],
            data['total_matches']
        )
