# teamsView.py

from discord import Interaction, Member, Message, ButtonStyle, Embed
from discord.ui import View, Button
from random import shuffle
from typing import List

from bot.bot import G5Bot


class PlayerButton(Button['PickTeamsView']):
    def __init__(self, user: Member):
        super().__init__(label=user.display_name, style=ButtonStyle.secondary)
        self.user = user

    async def callback(self, interaction: Interaction):
        await self.view.on_click_button(interaction, self)


class PickTeamsView(View):
    def __init__(self, bot: G5Bot, message: Message, users: List[Member], timeout=180):
        super().__init__(timeout=timeout)
        self.players_buttons = [PlayerButton(user) for user in users]
        for button in self.players_buttons:
            self.add_item(button)

        self.bot = bot
        self.message = message
        self.users = users
        self.pick_order = '1' + '2211' * 20
        self.pick_number = 0
        self.users_left = users.copy()
        self.teams = [[], []]
        self.future = None

    @property
    def _active_picker(self):
        try:
            picking_team_number = int(self.pick_order[self.pick_number])
            picking_team = self.teams[picking_team_number - 1]
            return picking_team[0] if picking_team else None
        except IndexError:
            return None

    def _pick_player(self, captain: Member, selected_player: Member):
        if captain == selected_player:
            return False

        if not self.teams[0]:
            picking_team = self.teams[0]
            self.users_left.remove(captain)
            picking_team.append(captain)
        elif self.teams[1] == [] and captain in self.teams[0]:
            return False
        elif not self.teams[1]:
            picking_team = self.teams[1]
            self.users_left.remove(captain)
            picking_team.append(captain)
        elif captain == self.teams[0][0]:
            picking_team = self.teams[0]
        elif captain == self.teams[1][0]:
            picking_team = self.teams[1]
        else:
            return False

        if captain != self._active_picker or len(picking_team) > len(self.users) // 2:
            return False

        self.users_left.remove(selected_player)
        picking_team.append(selected_player)
        self.pick_number += 1
        return True

    async def on_click_button(self, interaction: Interaction, button: PlayerButton):
        await interaction.response.defer()
        captain = interaction.user
        selected_player = button.user

        if selected_player is None or selected_player not in self.users_left or captain not in self.users:
            return

        if not self._pick_player(captain, selected_player):
            return

        self._remove_captain_button(captain)

        title = f"Team **{captain.display_name}** picked **{selected_player.display_name}**"

        if not self.users_left:
            embed = self.embed_teams_pick(title)
            await self.message.edit(embed=embed, view=None)
            self.stop()
            return

        self.remove_item(button)
        embed = self.embed_teams_pick(title)
        await self.message.edit(embed=embed, view=self)

    def _remove_captain_button(self, captain: Member):
        captain_button = next(
            (btn for btn in self.players_buttons if btn.user == captain), None)
        if captain_button:
            self.remove_item(captain_button)

    def embed_teams_pick(self, title: str):
        embed = Embed(title=title)
        str_info = ''

        for idx, team in enumerate(self.teams, start=1):
            team_name = f'__Team {idx}__'
            team_players = "*Empty*" if len(
                team) == 0 else '\n'.join(u.mention for u in team)
            embed.add_field(name=team_name, value=team_players)

        if self.users_left:
            str_info += f'Team1 captain: {self.teams[0][0].mention}\n' if len(
                self.teams[0]) else 'Team1 captain:\n'
            str_info += f'Team2 captain: {self.teams[1][0].mention}\n\n' if len(
                self.teams[1]) else 'Team2 captain:\n\n'
            str_info += f'Current turn: {self._active_picker.mention}' if self._active_picker is not None else 'Current turn: Any'
            embed.add_field(name="Picker Info", value=str_info)

        return embed

    async def start(self, captain_method: str):
        """"""
        if captain_method == 'rank':
            players_stats = await self.bot.db.get_players_stats([u.id for u in self.users])
            players_stats.sort(key=lambda x: x.rating, reverse=True)

            for team in self.teams:
                captain = players_stats.pop().member
                self.users_left.remove(captain)
                team.append(captain)
                self._remove_captain_button(captain)

        if captain_method == 'random':
            temp_users = self.users_left.copy()
            shuffle(temp_users)

            for team in self.teams:
                captain = temp_users.pop()
                self.users_left.remove(captain)
                team.append(captain)
                self._remove_captain_button(captain)

        if not self.users_left:
            self.stop()
