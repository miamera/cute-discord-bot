import discord
from discord import app_commands
from discord.ext import commands

from config import TICKET_FILE
from utils.storage import load_json, save_json


SPARK = "<a:00_spark:1547846651790626907>"

DEFAULT_DATA = {
    "tickets": {},
    "mass_completed": {},
    "hire_completed": {},
}


def get_mass_level(user_id: int):
    data = load_json(TICKET_FILE, DEFAULT_DATA)

    completed = int(
        data.get("mass_completed", {}).get(str(user_id), 0)
    )

    return min(completed, 5)


class Levels(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

    # ── /level ───────────────────────────────────────────────

    @app_commands.command(
        name="level",
        description="View your Mass level."
    )
    async def level(
        self,
        interaction: discord.Interaction,
    ):
        level = get_mass_level(interaction.user.id)

        await interaction.response.send_message(
            f"{SPARK} your mass level is **{level}/5**",
            ephemeral=True,
        )

    # ── /resetlevel ──────────────────────────────────────────

    @app_commands.command(
        name="resetlevel",
        description="Reset a user's Mass level."
    )
    @app_commands.describe(
        user="The user whose Mass level you want to reset."
    )
    @app_commands.default_permissions(
        manage_guild=True
    )
    async def resetlevel(
        self,
        interaction: discord.Interaction,
        user: discord.Member,
    ):
        if interaction.guild is None:
            await interaction.response.send_message(
                "♡ this command can only be used in a server.",
                ephemeral=True,
            )
            return

        if not interaction.user.guild_permissions.manage_guild:
            await interaction.response.send_message(
                "♡ you don't have permission to use this.",
                ephemeral=True,
            )
            return

        data = load_json(
            TICKET_FILE,
            DEFAULT_DATA,
        )

        mass_completed = data.setdefault(
            "mass_completed",
            {}
        )

        mass_completed[str(user.id)] = 0

        save_json(
            TICKET_FILE,
            data,
        )

        await interaction.response.send_message(
            f"{SPARK} reset {user.mention}'s Mass level to **0/5**.",
            ephemeral=True,
        )

    # ── /removelevel ─────────────────────────────────────────

    @app_commands.command(
        name="removelevel",
        description="Remove one Mass level from a user."
    )
    @app_commands.describe(
        user="The user whose Mass level you want to lower."
    )
    @app_commands.default_permissions(
        manage_guild=True
    )
    async def removelevel(
        self,
        interaction: discord.Interaction,
        user: discord.Member,
    ):
        if interaction.guild is None:
            await interaction.response.send_message(
                "♡ this command can only be used in a server.",
                ephemeral=True,
            )
            return

        if not interaction.user.guild_permissions.manage_guild:
            await interaction.response.send_message(
                "♡ you don't have permission to use this.",
                ephemeral=True,
            )
            return

        data = load_json(
            TICKET_FILE,
            DEFAULT_DATA,
        )

        mass_completed = data.setdefault(
            "mass_completed",
            {}
        )

        user_id = str(user.id)

        current = int(
            mass_completed.get(user_id, 0)
        )

        new_level = max(current - 1, 0)

        mass_completed[user_id] = new_level

        save_json(
            TICKET_FILE,
            data,
        )

        await interaction.response.send_message(
            f"{SPARK} removed 1 Mass level from "
            f"{user.mention} → **{min(new_level, 5)}/5**.",
            ephemeral=True,
        )


async def setup(bot):
    await bot.add_cog(Levels(bot))