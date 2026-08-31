import discord
from discord import app_commands
from config import Theme, Assets, FOOTER_TEXT

# --- from utils.embeds ---

def build_embed(title: str, description: str = None, color: int = Theme.PRIMARY) -> discord.Embed:
    """Helper function to create standardized beautiful embeds."""
    embed = discord.Embed(title=title, description=description, color=color)
    embed.set_footer(text=FOOTER_TEXT)
    embed.timestamp = discord.utils.utcnow()
    return embed

def build_error_embed(description: str) -> discord.Embed:
    """Helper function for error embeds."""
    return build_embed(title="❌ Error", description=description, color=Theme.ERROR)

def build_success_embed(description: str) -> discord.Embed:
    """Helper function for success embeds."""
    return build_embed(title="✅ Success", description=description, color=Theme.SUCCESS)

# --- from utils.permissions ---

def is_admin():
    """Check if the user is an administrator."""
    def predicate(interaction: discord.Interaction) -> bool:
        return interaction.user.guild_permissions.administrator
    return app_commands.check(predicate)

def is_moderator():
    """Check if the user has moderate_members permission or is admin."""
    def predicate(interaction: discord.Interaction) -> bool:
        perms = interaction.user.guild_permissions
        return perms.administrator or perms.moderate_members
    return app_commands.check(predicate)
