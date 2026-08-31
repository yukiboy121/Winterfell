# Winterfell Discord Bot

A production-ready, highly modular Discord bot built for House Stark using Python 3.12+ and discord.py 2.6+.

## Features

- **Slash Commands Only**: Built fully on Discord's modern application commands.
- **SQLite Database**: Uses `aiosqlite` for asynchronous database operations.
- **Welcome System**: Beautiful embed welcomes, auto-role assignment, and DMs.
- **Rotating Status**: Dynamically rotates bot presence every 15 seconds.
- **Custom Commands**: Admins can create dynamic custom text-responses on the fly.
- **Today Watch**: Movie announcement system using interactive Discord Modals and Buttons.
- **Ticket System**: Professional support panel with transcripts.
- **Reaction Roles**: Easily assign roles via reactions.
- **Giveaway System**: Host giveaways with automated winner selection.
- **Moderation & Logging**: Comprehensive moderation tools and event logging.

## Requirements

- Python 3.12+
- `discord.py` >= 2.6.0
- `aiosqlite` >= 0.20.0
- `python-dotenv`
- `psutil` (for system stats)

## Installation & Setup

1. **Clone the repository.**
2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```
3. **Configure the bot:**
   - Open `.env` and add your bot token: `DISCORD_TOKEN=your_token_here`
   - Review `config.py` to change theme colors or assets.
4. **Run the bot:**
   ```bash
   python bot.py
   ```
   *The SQLite database (`data/bot.db`) will be automatically created on first run.*

## Usage

Once the bot is online, use the `/settings setup` command as an Administrator to initialize the server in the database.
Then, you can use other commands to configure the welcome channel, log channel, ticket category, etc.

*Winter is Coming.*
