import os
import asyncio

import discord
from discord.ext import commands
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv("DISCORD_TOKEN")

if not TOKEN:
    raise RuntimeError(
        "DISCORD_TOKEN is missing from your .env file."
    )


# ─────────────────────────────────────────────
# INTENTS
# ─────────────────────────────────────────────

intents = discord.Intents.default()

intents.guilds = True
intents.members = True
intents.messages = True
intents.message_content = True
intents.reactions = True


# ─────────────────────────────────────────────
# BOT
# ─────────────────────────────────────────────

class CuteBot(commands.Bot):

    def __init__(self):
        super().__init__(
            command_prefix="!",
            intents=intents,
            help_command=None,
        )

    async def setup_hook(self):

        extensions = [
            "cogs.autoresponders",
            "cogs.help",
            "cogs.join_ping",
            "cogs.levels",
            "cogs.logs",
            "cogs.moderation",
            "cogs.reaction_roles",
            "cogs.reviews",
            "cogs.tickets",
            "cogs.variables",
        ]

        for extension in extensions:
            try:
                await self.load_extension(extension)
                print(f"Loaded: {extension}")
            except Exception as error:
                print(f"Failed to load {extension}: {error}")

        await self.tree.sync()

        print("Slash commands synced.")

    async def on_ready(self):
        print("────────────────────────────")
        print(f"Logged in as {self.user}")
        print(f"Bot ID: {self.user.id}")
        print("Bot is ready.")
        print("────────────────────────────")


bot = CuteBot()


@bot.event
async def on_command_error(ctx, error):

    if isinstance(error, commands.CommandNotFound):
        return

    print(f"Command error: {error}")


if __name__ == "__main__":
    asyncio.run(bot.start(TOKEN))