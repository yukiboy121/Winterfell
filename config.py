import discord
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Bot Token
TOKEN = os.getenv("DISCORD_TOKEN")
WELCOME_CHANNEL_ID = int(os.getenv("WELCOME_CHANNEL_ID", 0))
AUTO_ROLE_ID = int(os.getenv("AUTO_ROLE_ID", 0))
LOG_CHANNEL_ID = int(os.getenv("LOG_CHANNEL_ID", 0))

# Game of Thrones / Winterfell Theme Colors
class Theme:
    PRIMARY = 0x2B4B6F      # Dark Blue
    SECONDARY = 0x8A9AAB    # Silver/Grey
    DARK = 0x1A1A1A         # Dark mode background
    SUCCESS = 0x2ecc71      # Green for success
    ERROR = 0xe74c3c        # Red for errors
    WARNING = 0xf1c40f      # Yellow for warnings

# Assets
class Assets:
    THUMBNAIL_URL = "https://i.imgur.com/Kz6hUaU.png" # Placeholder Direwolf avatar
    BANNER_URL = "https://cdn.discordapp.com/attachments/1239166183111004200/1543857263062818876/the_fire_is_mine.gif?ex=6a96649e&is=6a95131e&hm=d1fc2c596b1bfa38de9ae405ceb1081bd3e79997984c9b81149a1d6e9584d8dc&"    # Placeholder Winterfell banner

# Bot Settings
COMMAND_PREFIX = "!"
BOT_NAME = "Winterfell"
FOOTER_TEXT = "Winterfell | House Stark"

# Intents configuration
def get_intents() -> discord.Intents:
    intents = discord.Intents.default()
    intents.message_content = True
    intents.members = True
    intents.presences = True
    return intents
