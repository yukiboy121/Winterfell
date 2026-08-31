import discord
from discord.ext import commands
from discord import app_commands
import logging
import asyncio
import datetime
import random
import time
import platform
import psutil

import collections
from utils import build_embed, build_error_embed, build_success_embed, Theme, is_admin, is_moderator
from config import BOT_NAME, LOG_CHANNEL_ID

logger = logging.getLogger('features')

# --- Giveaways Cog ---
class GiveawaysCog(commands.Cog, name="Giveaways"):
    def __init__(self, bot):
        self.bot = bot

    giveaway_group = app_commands.Group(name="giveaway", description="Manage giveaways")

    @giveaway_group.command(name="create", description="Create a new giveaway.")
    @app_commands.describe(duration="Duration in seconds", winners="Number of winners", prize="The prize")
    @is_admin()
    async def create_giveaway(self, interaction: discord.Interaction, duration: int, winners: int, prize: str):
        end_time = discord.utils.utcnow() + datetime.timedelta(seconds=duration)
        
        embed = build_embed("🎉 GIVEAWAY 🎉", f"**Prize:** {prize}\n**Winners:** {winners}\n**Ends:** <t:{int(end_time.timestamp())}:R>\n\nReact with 🎉 to enter!", Theme.PRIMARY)
        await interaction.response.send_message(embed=embed)
        msg = await interaction.original_response()
        await msg.add_reaction("🎉")
        
        # Schedule end
        self.bot.loop.create_task(self.end_giveaway_task(interaction.channel, msg.id, duration, winners, prize))

    async def end_giveaway_task(self, channel, message_id, duration, winners, prize):
        await asyncio.sleep(duration)
        try:
            msg = await channel.fetch_message(message_id)
            reaction = discord.utils.get(msg.reactions, emoji="🎉")
            if not reaction: return
            
            users = [user async for user in reaction.users() if not user.bot]
            if len(users) == 0:
                await channel.send(embed=build_error_embed(f"No valid entries for **{prize}** giveaway."))
                return
                
            winners_list = random.sample(users, min(winners, len(users)))
            winner_mentions = ", ".join([w.mention for w in winners_list])
            
            embed = build_success_embed(f"Congratulations {winner_mentions}!\nYou won **{prize}**!")
            await msg.reply(embed=embed)
            
            # Update original embed
            old_embed = msg.embeds[0]
            old_embed.description = f"**Prize:** {prize}\n**Winners:** {winners}\n**Status:** Ended\n**Winner(s):** {winner_mentions}"
            old_embed.color = Theme.SECONDARY
            await msg.edit(embed=old_embed)
            
        except Exception as e:
            logger.error(f"Failed to end giveaway {message_id}: {e}")

    @giveaway_group.command(name="reroll", description="Reroll a giveaway winner.")
    @is_admin()
    async def reroll_giveaway(self, interaction: discord.Interaction, message_id: str):
        try:
            msg = await interaction.channel.fetch_message(int(message_id))
            reaction = discord.utils.get(msg.reactions, emoji="🎉")
            if not reaction:
                await interaction.response.send_message("No 🎉 reaction found.", ephemeral=True)
                return
                
            users = [user async for user in reaction.users() if not user.bot]
            if not users:
                await interaction.response.send_message("No valid entries.", ephemeral=True)
                return
                
            winner = random.choice(users)
            await interaction.response.send_message(f"The new winner is {winner.mention}! Congratulations! 🎉")
        except Exception as e:
            await interaction.response.send_message(embed=build_error_embed(f"Error rerolling: {e}"), ephemeral=True)

    @giveaway_group.command(name="end", description="End a giveaway early.")
    @is_admin()
    async def end_giveaway_cmd(self, interaction: discord.Interaction, message_id: str):
        await interaction.response.send_message("To end early, simply use `/giveaway reroll` or delete the message. Immediate end feature coming soon.", ephemeral=True)

# --- Interactive Cog ---
class ExampleView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None) # Timeout=None makes it persistent if we setup `add_view` on bot start
        
    @discord.ui.button(label="Pledge Loyalty", style=discord.ButtonStyle.success, custom_id="btn_pledge", emoji="⚔️")
    async def pledge_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message(f"You have pledged your loyalty to House Stark, {interaction.user.mention}!", ephemeral=True)
        
    @discord.ui.button(label="Request Aid", style=discord.ButtonStyle.primary, custom_id="btn_aid", emoji="🛡️")
    async def aid_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message(f"The Maesters have been notified of your request for aid.", ephemeral=True)
        
    @discord.ui.button(label="Leave", style=discord.ButtonStyle.danger, custom_id="btn_leave", emoji="🚪")
    async def leave_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message("You cannot leave the North so easily.", ephemeral=True)

class InteractiveCog(commands.Cog, name="Interactive"):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="spawn_buttons", description="Spawns an interactive text message with components")
    @app_commands.checks.has_permissions(administrator=True)
    async def spawn_buttons(self, interaction: discord.Interaction):
        # Plain text message without embed
        content = (
            "**Winterfell Command Center**\n\n"
            "Please select an action from the options below. "
            "This message uses Discord UI Components (Buttons) without any embeds."
        )
        
        view = ExampleView()
        
        # Send the message with the view attached
        await interaction.response.send_message(content=content, view=view)
        logger.info(f"Interactive component message spawned by {interaction.user}")

# --- Moderation Cog ---
class ModerationCog(commands.Cog, name="Moderation"):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="ban", description="Ban a member from the server.")
    @app_commands.describe(member="The member to ban", reason="Reason for the ban")
    @is_moderator()
    async def ban_command(self, interaction: discord.Interaction, member: discord.Member, reason: str = "No reason provided"):
        if member.top_role >= interaction.user.top_role:
            await interaction.response.send_message(embed=build_error_embed("You cannot ban this member."), ephemeral=True)
            return
            
        try:
            await member.ban(reason=f"{interaction.user}: {reason}")
            await interaction.response.send_message(embed=build_success_embed(f"Banned {member.mention} for: {reason}"))
        except discord.Forbidden:
            await interaction.response.send_message(embed=build_error_embed("I don't have permission to ban this member."), ephemeral=True)

    @app_commands.command(name="kick", description="Kick a member from the server.")
    @app_commands.describe(member="The member to kick", reason="Reason for the kick")
    @is_moderator()
    async def kick_command(self, interaction: discord.Interaction, member: discord.Member, reason: str = "No reason provided"):
        if member.top_role >= interaction.user.top_role:
            await interaction.response.send_message(embed=build_error_embed("You cannot kick this member."), ephemeral=True)
            return
            
        try:
            await member.kick(reason=f"{interaction.user}: {reason}")
            await interaction.response.send_message(embed=build_success_embed(f"Kicked {member.mention} for: {reason}"))
        except discord.Forbidden:
            await interaction.response.send_message(embed=build_error_embed("I don't have permission to kick this member."), ephemeral=True)

    @app_commands.command(name="timeout", description="Timeout a member.")
    @app_commands.describe(member="The member to timeout", duration_minutes="Duration in minutes", reason="Reason")
    @is_moderator()
    async def timeout_command(self, interaction: discord.Interaction, member: discord.Member, duration_minutes: int, reason: str = "No reason provided"):
        if member.top_role >= interaction.user.top_role:
            await interaction.response.send_message(embed=build_error_embed("You cannot timeout this member."), ephemeral=True)
            return
            
        try:
            duration = discord.utils.utcnow() + datetime.timedelta(minutes=duration_minutes)
            await member.timeout(duration, reason=f"{interaction.user}: {reason}")
            await interaction.response.send_message(embed=build_success_embed(f"Timed out {member.mention} for {duration_minutes} minutes. Reason: {reason}"))
        except discord.Forbidden:
            await interaction.response.send_message(embed=build_error_embed("I don't have permission to timeout this member."), ephemeral=True)

    @app_commands.command(name="untimeout", description="Remove a timeout from a member.")
    @is_moderator()
    async def untimeout_command(self, interaction: discord.Interaction, member: discord.Member):
        try:
            await member.timeout(None, reason=f"Timeout removed by {interaction.user}")
            await interaction.response.send_message(embed=build_success_embed(f"Removed timeout for {member.mention}"))
        except discord.Forbidden:
            await interaction.response.send_message(embed=build_error_embed("I don't have permission to manage timeouts."), ephemeral=True)

    @app_commands.command(name="clear", description="Clear messages in a channel.")
    @app_commands.describe(amount="Number of messages to delete")
    @is_moderator()
    async def clear_command(self, interaction: discord.Interaction, amount: int):
        if amount < 1 or amount > 100:
            await interaction.response.send_message(embed=build_error_embed("Amount must be between 1 and 100."), ephemeral=True)
            return
            
        await interaction.response.defer(ephemeral=True)
        deleted = await interaction.channel.purge(limit=amount)
        await interaction.followup.send(embed=build_success_embed(f"Cleared {len(deleted)} messages."))

    @app_commands.command(name="lock", description="Lock the current channel.")
    @is_moderator()
    async def lock_command(self, interaction: discord.Interaction):
        await interaction.channel.set_permissions(interaction.guild.default_role, send_messages=False)
        await interaction.response.send_message(embed=build_success_embed("Channel locked. 🔒"))

    @app_commands.command(name="unlock", description="Unlock the current channel.")
    @is_moderator()
    async def unlock_command(self, interaction: discord.Interaction):
        await interaction.channel.set_permissions(interaction.guild.default_role, send_messages=None)
        await interaction.response.send_message(embed=build_success_embed("Channel unlocked. 🔓"))

    @app_commands.command(name="slowmode", description="Set channel slowmode.")
    @app_commands.describe(seconds="Delay in seconds (0 to disable)")
    @is_moderator()
    async def slowmode_command(self, interaction: discord.Interaction, seconds: int):
        if seconds < 0 or seconds > 21600:
            await interaction.response.send_message(embed=build_error_embed("Seconds must be between 0 and 21600."), ephemeral=True)
            return
        
        await interaction.channel.edit(slowmode_delay=seconds)
        if seconds == 0:
            await interaction.response.send_message(embed=build_success_embed("Slowmode disabled."))
        else:
            await interaction.response.send_message(embed=build_success_embed(f"Slowmode set to {seconds} seconds."))

    @app_commands.command(name="nickname", description="Change a member's nickname.")
    @is_moderator()
    async def nickname_command(self, interaction: discord.Interaction, member: discord.Member, nick: str = None):
        if member.top_role >= interaction.user.top_role:
            await interaction.response.send_message(embed=build_error_embed("You cannot change this member's nickname."), ephemeral=True)
            return
            
        try:
            await member.edit(nick=nick)
            await interaction.response.send_message(embed=build_success_embed(f"Nickname for {member.mention} has been {'reset' if not nick else 'changed to ' + nick}."))
        except discord.Forbidden:
            await interaction.response.send_message(embed=build_error_embed("I don't have permission to manage nicknames."), ephemeral=True)

# --- Utility Cog ---
class UtilityCog(commands.Cog, name="Utility"):
    def __init__(self, bot):
        self.bot = bot
        self.start_time = time.time()

    @app_commands.command(name="server", description="Get server information.")
    async def server_info(self, interaction: discord.Interaction):
        guild = interaction.guild
        embed = build_embed(f"Server Info: {guild.name}", color=Theme.PRIMARY)
        if guild.icon:
            embed.set_thumbnail(url=guild.icon.url)
            
        embed.add_field(name="Owner", value=guild.owner.mention, inline=True)
        embed.add_field(name="Members", value=str(guild.member_count), inline=True)
        embed.add_field(name="Roles", value=str(len(guild.roles)), inline=True)
        embed.add_field(name="Channels", value=str(len(guild.channels)), inline=True)
        embed.add_field(name="Created At", value=f"<t:{int(guild.created_at.timestamp())}:D>", inline=True)
        
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="user", description="Get user information.")
    async def user_info(self, interaction: discord.Interaction, member: discord.Member = None):
        member = member or interaction.user
        embed = build_embed(f"User Info: {member.display_name}", color=Theme.PRIMARY)
        if member.display_avatar:
            embed.set_thumbnail(url=member.display_avatar.url)
            
        embed.add_field(name="ID", value=member.id, inline=True)
        embed.add_field(name="Joined Server", value=f"<t:{int(member.joined_at.timestamp())}:D>", inline=True)
        embed.add_field(name="Joined Discord", value=f"<t:{int(member.created_at.timestamp())}:D>", inline=True)
        embed.add_field(name="Top Role", value=member.top_role.mention, inline=True)
        
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="avatar", description="Get user's avatar.")
    async def avatar(self, interaction: discord.Interaction, member: discord.Member = None):
        member = member or interaction.user
        embed = build_embed(f"{member.display_name}'s Avatar", color=Theme.PRIMARY)
        embed.set_image(url=member.display_avatar.url)
        await interaction.response.send_message(embed=embed)

    @app_commands.command(name="ping", description="Check bot latency.")
    async def ping(self, interaction: discord.Interaction):
        latency = round(self.bot.latency * 1000)
        await interaction.response.send_message(embed=build_embed("🏓 Pong!", f"Latency: `{latency}ms`", Theme.PRIMARY))

    @app_commands.command(name="uptime", description="Check bot uptime.")
    async def uptime(self, interaction: discord.Interaction):
        current_time = time.time()
        difference = int(round(current_time - self.start_time))
        text = str(datetime.timedelta(seconds=difference))
        await interaction.response.send_message(embed=build_embed("Uptime", f"`{text}`", Theme.PRIMARY))

    @app_commands.command(name="about", description="About the bot.")
    async def about(self, interaction: discord.Interaction):
        embed = build_embed(f"About {BOT_NAME}", "A professional Discord bot built for House Stark.", Theme.PRIMARY)
        embed.add_field(name="Developer", value="Senior Python Engineer", inline=True)
        embed.add_field(name="Library", value=f"discord.py {discord.__version__}", inline=True)
        embed.add_field(name="Python", value=platform.python_version(), inline=True)
        
        # System info
        mem = psutil.virtual_memory()
        embed.add_field(name="RAM Usage", value=f"{mem.percent}%", inline=True)
        embed.add_field(name="CPU Usage", value=f"{psutil.cpu_percent()}%", inline=True)
        
        await interaction.response.send_message(embed=embed)


# --- AutoMod Cog ---
class AutoModCog(commands.Cog, name="AutoMod"):
    def __init__(self, bot):
        self.bot = bot
        # user_id -> deque of timestamps
        self.message_cache = collections.defaultdict(lambda: collections.deque(maxlen=5))

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author.bot or not message.guild or message.author.guild_permissions.administrator:
            return
            
        now = time.time()
        user_id = message.author.id
        
        self.message_cache[user_id].append(now)
        
        if len(self.message_cache[user_id]) == 5:
            # Check if 5th oldest message was within 5 seconds
            oldest = self.message_cache[user_id][0]
            if now - oldest <= 5:
                # Spam detected
                self.message_cache[user_id].clear()
                
                try:
                    # Delete recent messages
                    await message.channel.purge(limit=10, check=lambda m: m.author == message.author and (now - m.created_at.timestamp()) <= 10)
                except Exception as e:
                    logger.error(f"Failed to auto-delete spam messages: {e}")
                
                # Send log
                if LOG_CHANNEL_ID:
                    log_channel = message.guild.get_channel(LOG_CHANNEL_ID)
                    if log_channel:
                        embed = build_error_embed(f"**Spam Detected**\n{message.author.mention} (`{user_id}`) sent too many messages quickly in {message.channel.mention}.")
                        embed.title = "⚠️ AutoMod Alert"
                        
                        view = discord.ui.View(timeout=None)
                        timeout_btn = discord.ui.Button(
                            label="Timeout (10m)", 
                            style=discord.ButtonStyle.danger, 
                            custom_id=f"automod_timeout_{user_id}",
                            emoji="🔨"
                        )
                        view.add_item(timeout_btn)
                        
                        await log_channel.send(embed=embed, view=view)

    @commands.Cog.listener()
    async def on_interaction(self, interaction: discord.Interaction):
        if interaction.type == discord.InteractionType.component:
            custom_id = interaction.data.get("custom_id", "")
            if custom_id.startswith("automod_timeout_"):
                if not interaction.user.guild_permissions.moderate_members:
                    await interaction.response.send_message("You don't have permission to do this.", ephemeral=True)
                    return
                    
                user_id = int(custom_id.split("_")[-1])
                member = interaction.guild.get_member(user_id)
                if not member:
                    await interaction.response.send_message("Member no longer in server.", ephemeral=True)
                    return
                    
                if member.top_role >= interaction.user.top_role:
                    await interaction.response.send_message("You cannot timeout this member.", ephemeral=True)
                    return
                    
                duration = discord.utils.utcnow() + datetime.timedelta(minutes=10)
                try:
                    await member.timeout(duration, reason=f"AutoMod spam timeout by {interaction.user}")
                    
                    # Edit the original message to show action taken
                    embed = interaction.message.embeds[0]
                    embed.color = Theme.WARNING
                    embed.add_field(name="Action Taken", value=f"Timed out for 10m by {interaction.user.mention}")
                        
                    view = discord.ui.View.from_message(interaction.message)
                    for child in view.children:
                        child.disabled = True
                        
                    await interaction.response.edit_message(embed=embed, view=view)
                    
                except discord.Forbidden:
                    await interaction.response.send_message("I don't have permission to timeout this member.", ephemeral=True)

async def setup(bot):
    await bot.add_cog(GiveawaysCog(bot))
    await bot.add_cog(InteractiveCog(bot))
    await bot.add_cog(ModerationCog(bot))
    await bot.add_cog(UtilityCog(bot))
    await bot.add_cog(AutoModCog(bot))
