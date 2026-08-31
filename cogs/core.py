import discord
from discord.ext import commands, tasks
from discord import app_commands
import itertools
import logging

from utils import build_embed, build_error_embed, Theme
from config import BOT_NAME, Assets, WELCOME_CHANNEL_ID, AUTO_ROLE_ID

logger = logging.getLogger('core')

# --- Help Cog ---
class HelpCog(commands.Cog, name="Help"):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="help", description="Show all available commands.")
    async def help_command(self, interaction: discord.Interaction):
        embed = build_embed(f"{BOT_NAME} Commands", "Here are the available command categories.", Theme.PRIMARY)
        
        for cog_name, cog in self.bot.cogs.items():
            if cog_name in ["ErrorHandler", "Help"]:
                continue
                
            cmd_list = []
            
            for cmd in cog.get_app_commands():
                if isinstance(cmd, app_commands.Group):
                    for subcmd in cmd.commands:
                        cmd_list.append(f"`/{cmd.name} {subcmd.name}` - {subcmd.description}")
                else:
                    cmd_list.append(f"`/{cmd.name}` - {cmd.description}")
            
            if cmd_list:
                embed.add_field(name=f"**{cog_name}**", value="\n".join(cmd_list), inline=False)
                
        await interaction.response.send_message(embed=embed, ephemeral=True)

# --- Error Handler Cog ---
class ErrorHandler(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        bot.tree.on_error = self.on_app_command_error

    async def on_app_command_error(self, interaction: discord.Interaction, error: discord.app_commands.AppCommandError):
        """Global error handler for app commands (slash commands)."""
        logger.error(f"App command error in {interaction.command}: {error}")
        
        embed = None
        if isinstance(error, discord.app_commands.MissingPermissions):
            embed = build_error_embed(f"You don't have the required permissions to use this command.\nMissing: `{', '.join(error.missing_permissions)}`")
        elif isinstance(error, discord.app_commands.BotMissingPermissions):
            embed = build_error_embed(f"I don't have the required permissions to execute this command.\nMissing: `{', '.join(error.missing_permissions)}`")
        elif isinstance(error, discord.app_commands.CommandOnCooldown):
            embed = build_error_embed(f"This command is on cooldown. Try again in `{error.retry_after:.2f}s`.")
        else:
            embed = build_error_embed(f"An unexpected error occurred: `{error}`")
            
        if not interaction.response.is_done():
            await interaction.response.send_message(embed=embed, ephemeral=True)
        else:
            await interaction.followup.send(embed=embed, ephemeral=True)

    @commands.Cog.listener()
    async def on_command_error(self, ctx: commands.Context, error: commands.CommandError):
        """Global error handler for text commands."""
        if isinstance(error, commands.CommandNotFound):
            return
            
        logger.error(f"Text command error in {ctx.command}: {error}")
        
        embed = None
        if isinstance(error, commands.MissingPermissions):
            embed = build_error_embed(f"You don't have the required permissions.\nMissing: `{', '.join(error.missing_permissions)}`")
        elif isinstance(error, commands.BotMissingPermissions):
            embed = build_error_embed(f"I don't have the required permissions.\nMissing: `{', '.join(error.missing_permissions)}`")
        elif isinstance(error, commands.MissingRequiredArgument):
            embed = build_error_embed(f"Missing required argument: `{error.param.name}`")
        else:
            embed = build_error_embed(f"An error occurred: `{error}`")
            
        await ctx.send(embed=embed)

# --- Status Cog ---
class StatusCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        # Define the statuses to rotate through
        self.statuses = itertools.cycle([
            discord.Activity(type=discord.ActivityType.watching, name="Winter Is Coming"),
            discord.Activity(type=discord.ActivityType.listening, name="North Remembers"),
            discord.Activity(type=discord.ActivityType.listening, name="to the howling wind")
        ])

    @commands.Cog.listener()
    async def on_ready(self):
        if not self.status_task.is_running():
            self.status_task.start()
            logger.info("Started rotating status task.")

    @tasks.loop(seconds=30)
    async def status_task(self):
        try:
            status = next(self.statuses)
            await self.bot.change_presence(activity=status)
        except Exception as e:
            logger.error(f"Failed to update status: {e}")

    @status_task.before_loop
    async def before_status_task(self):
        await self.bot.wait_until_ready()

# --- Welcome Cog ---
class WelcomeCog(commands.Cog, name="Welcome"):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member):
        guild = member.guild
        
        # Auto Role
        if AUTO_ROLE_ID:
            role = guild.get_role(AUTO_ROLE_ID)
            if role:
                try:
                    await member.add_roles(role)
                    logger.info(f"Assigned auto-role {role.name} to {member.name}")
                except discord.Forbidden:
                    logger.error(f"Missing permissions to assign role {role.name} to {member.name}")
                except discord.HTTPException as e:
                    logger.error(f"Failed to assign auto-role: {e}")
            else:
                logger.warning(f"Auto-role with ID {AUTO_ROLE_ID} not found in {guild.name}")
        
        # Check if welcome channel is configured
        if not WELCOME_CHANNEL_ID:
            logger.warning("Welcome channel not configured in .env")
            return
            
        channel = guild.get_channel(WELCOME_CHANNEL_ID)
        if not channel:
            logger.warning(f"Welcome channel {WELCOME_CHANNEL_ID} not found in {guild.name}")
            return
            
        # Create a Unique, Minimal Embed
        embed = discord.Embed(
            title=f"A New Northman Joins the Pack",
            description=f"Welcome to Winterfell, {member.mention}.\n\nThe winds of winter blow cold, but our hearths burn warm. Stand with us, for the lone wolf dies, but the pack survives.",
            color=Theme.PRIMARY
        )
        
        # User details
        avatar_url = member.display_avatar.url if member.display_avatar else Assets.THUMBNAIL_URL
        embed.set_thumbnail(url=avatar_url)
        embed.set_image(url=Assets.BANNER_URL)
        
        try:
            # Minimal mention outside the embed
            await channel.send(content=f"Hail, {member.mention}", embed=embed)
            logger.info(f"Sent welcome message for {member.name}")
        except Exception as e:
            logger.error(f"Failed to send welcome message: {e}")


async def setup(bot):
    await bot.add_cog(HelpCog(bot))
    await bot.add_cog(ErrorHandler(bot))
    await bot.add_cog(StatusCog(bot))
    await bot.add_cog(WelcomeCog(bot))
