# confirmView.py

from discord.ui import View, Button, button
from discord import Interaction, Member, ButtonStyle

class ConfirmView(View):
    """A view that displays two buttons for accepting or rejecting an action."""

    def __init__(self, target_user: Member, timeout: float = 60.0):
        """ Initialize the view with a target user and a timeout. """
        super().__init__(timeout=timeout)
        self.target_user = target_user
        self.accepted = None  # This will store the user's decision

    async def on_timeout(self):
        """ Handle the timeout event. """
        self.accepted = False  # Default to rejection on timeout
        self.stop()

    @button(label='Accept', style=ButtonStyle.green)
    async def accept(self, interaction: Interaction, button: Button):
        """ Handle the accept button click. """
        if interaction.user != self.target_user:
            await interaction.response.send_message("You are not authorized to do this.", ephemeral=True)
            return
        self.accepted = True
        self.stop()

    @button(label='Reject', style=ButtonStyle.red)
    async def reject(self, interaction: Interaction, button: Button):
        """ Handle the reject button click. """
        if interaction.user != self.target_user:
            await interaction.response.send_message("You are not authorized to do this.", ephemeral=True)
            return
        self.accepted = False
        self.stop()

    async def interaction_check(self, interaction: Interaction) -> bool:
        """ Check if the interacting user is the target user. """
        if interaction.user != self.target_user:
            await interaction.response.send_message("You are not allowed to interact with this!", ephemeral=True)
            return False
        return True