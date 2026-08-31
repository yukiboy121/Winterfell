import discord
from discord.ext import commands
import os
import asyncio
import logging

from config import TOKEN, get_intents

# Configure Logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('bot')

class WinterfellBot(commands.Bot):
    def __init__(self):
        super().__init__(
            command_prefix=commands.when_mentioned,
            intents=get_intents(),
            help_command=None # We will use our own custom help cog
        )
    async def setup_hook(self):
        
        # Load Cogs
        cogs_dir = './cogs'
        for filename in os.listdir(cogs_dir):
            if filename.endswith('.py') and not filename.startswith('_'):
                try:
                    await self.load_extension(f'cogs.{filename[:-3]}')
                    logger.info(f"Loaded cog: {filename}")
                except Exception as e:
                    logger.error(f"Failed to load cog {filename}: {e}")
                    
        # Sync Slash Commands
        logger.info("Syncing slash commands...")
        try:
            synced = await self.tree.sync()
            logger.info(f"Synced {len(synced)} command(s) globally.")
        except Exception as e:
            logger.error(f"Failed to sync commands: {e}")

    async def on_ready(self):
        logger.info(f"Logged in as {self.user} (ID: {self.user.id})")
        logger.info("Winter is Coming!")

bot = WinterfellBot()

if __name__ == "__main__":
    if not TOKEN:
        logger.error("DISCORD_TOKEN is missing in .env file.")
    else:
        bot.run(TOKEN)
