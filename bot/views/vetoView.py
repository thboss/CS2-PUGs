# vetoView.py

from discord import Interaction, Member, Message, ButtonStyle, Embed
from discord.ui import View, Button
import asyncio
from typing import List

from bot.resources import Config


class MapButton(Button['VetoView']):
    def __init__(self, selected_map: str, display_name: str):
        super().__init__(style=ButtonStyle.secondary,
                         label=display_name)
        self.selected_map = selected_map

    async def callback(self, interaction: Interaction):
        await self.view.on_click_button(interaction, self)


class VetoView(View):
    def __init__(self,
        message: Message,
        mpool: List[str],
        captain1: Member,
        captain2: Member,
        timeout=180
    ):
        super().__init__(timeout=timeout)
        self.message = message
        self.captains = [captain1, captain2]
        self.ban_order = '12' * 20
        self.ban_number = 0
        self.maps_left = mpool
        for m in mpool:
            self.add_item(MapButton(m, Config.maps[m]))

    @property
    def _active_picker(self):
        picking_player_number = int(self.ban_order[self.ban_number])
        return self.captains[picking_player_number - 1]

    @property
    def is_veto_done(self):
        return len(self.maps_left) == 1
    
    async def on_timeout(self):
        raise asyncio.TimeoutError
    
    async def interaction_check(self, interaction: Interaction):
        await interaction.response.defer()
        if interaction.user != self._active_picker:
            return False
        return True

    def embed_veto(self, title: str="Map veto begun!"):
        """"""
        description = f"**Captain 1:** {self.captains[0].mention}\n" \
            f"**Captain 2:** {self.captains[1].mention}\n\n" \
            f"**Current Turn:** {self._active_picker.mention}"
        embed = Embed(title=title, description=description)
        return embed

    async def on_click_button(self, interaction: Interaction, button: MapButton):
        user = interaction.user
        selected_map = button.selected_map
        if selected_map not in self.maps_left:
            return
    
        self.maps_left.remove(selected_map)

        button.style = ButtonStyle.danger
        button.disabled = True

        self.ban_number += 1

        title = f"Player {user.display_name} **banned** map **{Config.maps[selected_map]}**"
        embed = self.embed_veto(title)
        await self.message.edit(embed=embed, view=None if self.is_veto_done else self)

        if self.is_veto_done:
            self.stop()


