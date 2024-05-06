from discord.app_commands import AppCommandError
from discord import Member, Interaction, Embed, app_commands
from discord.errors import Forbidden
import logging


class CustomError(AppCommandError):
    """ A custom error that is raised when a command encountres an issue. """

    def __init__(self, message: str=None):
        if not message:
            message = "Unknown error occurred."
        self.message = message
        super().__init__(message)


class APIError(AppCommandError):
    """ A custom error that is raised when a command encountres an issue with API. """

    def __init__(self, message: str=None):
        if not message:
            message = "Something went wrong with API call."
        self.message = message
        super().__init__(message)


class JoinLobbyError(ValueError):
    """ Raised when a player can't join lobby for some reason. """

    def __init__(self, user: Member, reason: str):
        """ Set message parameter. """
        self.message = f"Unable to add **{user.display_name}**: " + reason


async def on_app_command_error(interaction: Interaction, error: app_commands.AppCommandError) -> None:
    """ Executed every time a slash command catches an error. """

    if isinstance(error, app_commands.CommandOnCooldown):
        minutes, seconds = divmod(error.retry_after, 60)
        hours, minutes = divmod(minutes, 60)
        hours = hours % 24
        hours = f'{round(hours)} hours ' if round(hours) > 0 else ''
        minutes = f'{round(minutes)} minutes ' if round(minutes) > 0 else ''
        seconds = f'{round(seconds)} seconds ' if round(seconds) > 0 else ''
        description = f"**Please slow down** - You can use this command again in {hours}{minutes}{seconds}"
    elif isinstance(error, (CustomError, APIError)):
        description = error.message
    elif isinstance(error, app_commands.MissingPermissions):
        description = "You are missing the permission(s) `" \
            + ", ".join(error.missing_permissions) \
            + "` to execute this command!"
    elif isinstance(error, (app_commands.BotMissingPermissions, Forbidden)):
        description = "I am missing the permission(s) `" \
            + ", ".join(error.missing_permissions) \
            + "` to fully perform this command!"
    else:
        logger = logging.getLogger('Bot')
        description = "Something went wrong, check logs for more details."
        logger.error(f'Unhandled exception in "/{interaction.command.name}" command: ', error, exc_info=1)
        
    embed = Embed(description=description, color=0xE02B2B)

    if not interaction.response.is_done():
        await interaction.response.defer()

    await interaction.edit_original_response(embed=embed, view=None)
