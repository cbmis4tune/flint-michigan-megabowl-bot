import os

import discord
from discord.ext import commands
from dotenv import load_dotenv
from database.database import initialize_database


load_dotenv()


class MegabowlBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()

        super().__init__(
            command_prefix="!",
            intents=intents,
        )

    async def setup_hook(self):
        initialize_database()
        
        await self.load_extension("cogs.league")
        await self.load_extension("cogs.scheduler")
        await self.load_extension("cogs.draft")
        await self.load_extension("cogs.member_management")
        await self.load_extension("cogs.feature_request")
        await self.load_extension("cogs.bug_reports")

        await self.tree.sync()


bot = MegabowlBot()


@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")
    print("Bot is ready!")


discord_token = os.getenv("DISCORD_TOKEN")

if not discord_token:
    raise ValueError("DISCORD_TOKEN is missing from .env")


bot.run(discord_token)