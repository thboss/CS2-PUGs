# readyView.py

from discord import Interaction, Member, TextChannel, ButtonStyle, Embed
from discord.ui import View, Button, button
from typing import List

class ReadyView(View):
    """ A view for Discord users to indicate they are ready for an event. """

    def __init__(self, users: List[Member], channel: TextChannel, timeout: float = 60.0):
        """ Initialize the view with a list of users, a target channel, and a timeout. """
        super().__init__(timeout=timeout)
        self.users = users
        self.channel = channel
        self.ready_users = set()
        self.message = None

    @property
    def all_ready(self) -> bool:
        return self.ready_users.issuperset(self.users)

    async def on_timeout(self):
        if self.message:
            await self.message.delete()

    async def interaction_check(self, interaction: Interaction) -> bool:
        """ Ensure that only the specified users can interact with the view. """
        if interaction.user not in self.users or interaction.user in self.ready_users:
            await interaction.response.defer()
            return False
        return True

    @button(label='Ready', style=ButtonStyle.green)
    async def ready(self, interaction: Interaction, button: Button):
        """ Handle the ready button click. """
        self.ready_users.add(interaction.user)
        await self.update_message()
        await interaction.response.defer()
        if self.all_ready:
            self.stop()
            await self.message.delete()

    async def update_message(self):
        """ Update the message to reflect the current ready status of users. """
        if self.message:
            await self.message.edit(embed=self.create_embed())

    def create_embed(self) -> Embed:
        """ Create an embed showing the ready status of each user. """
        embed = Embed(title="Lobby Status", description="Click the button when you are ready.")
        for num, user in enumerate(self.users, start=1):
            status = "✅ Ready" if user in self.ready_users else "❌ Not Ready"
            embed.add_field(name=f"{num}. {user.display_name}", value=status, inline=False)
        return embed

    async def start(self):
        """ Send the initial message and add the view to it. """
        self.message = await self.channel.send(
            content=''.join(u.mention for u in self.users),
            embed=self.create_embed(),
            view=self
        )