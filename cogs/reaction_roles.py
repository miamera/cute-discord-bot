import discord
from discord import app_commands
from discord.ext import commands

from config import REACTION_ROLE_FILE
from utils.storage import load_json, save_json


class ReactionRoles(commands.Cog):

    def __init__(self, bot):
        self.bot = bot
        self.data = load_json(
            REACTION_ROLE_FILE,
            {}
        )

    reactionrole = app_commands.Group(
        name="reactionrole",
        description="Manage reaction roles."
    )

    @reactionrole.command(
        name="add",
        description="Add a reaction role configuration."
    )
    @app_commands.checks.has_permissions(
        manage_roles=True
    )
    async def add(
        self,
        interaction: discord.Interaction,
        message_id: str,
        emoji: str,
        role: discord.Role,
    ):

        guild_id = str(interaction.guild.id)

        if guild_id not in self.data:
            self.data[guild_id] = {}

        if message_id not in self.data[guild_id]:
            self.data[guild_id][message_id] = []

        self.data[guild_id][message_id].append({
            "emoji": emoji,
            "role_id": role.id,
            "type": "reaction",
        })

        save_json(
            REACTION_ROLE_FILE,
            self.data
        )

        await interaction.response.send_message(
            f"♡ {emoji} → {role.mention} added.",
            ephemeral=True,
        )

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload):

        guild_data = self.data.get(
            str(payload.guild_id),
            {}
        )

        message_data = guild_data.get(
            str(payload.message_id),
            []
        )

        guild = self.bot.get_guild(
            payload.guild_id
        )

        if not guild:
            return

        member = guild.get_member(
            payload.user_id
        )

        if not member or member.bot:
            return

        emoji = str(payload.emoji)

        for item in message_data:

            if item["emoji"] != emoji:
                continue

            role = guild.get_role(
                item["role_id"]
            )

            if role:
                try:
                    await member.add_roles(role)
                except discord.HTTPException:
                    pass

    @commands.Cog.listener()
    async def on_raw_reaction_remove(self, payload):

        guild_data = self.data.get(
            str(payload.guild_id),
            {}
        )

        message_data = guild_data.get(
            str(payload.message_id),
            []
        )

        guild = self.bot.get_guild(
            payload.guild_id
        )

        if not guild:
            return

        member = guild.get_member(
            payload.user_id
        )

        if not member:
            return

        emoji = str(payload.emoji)

        for item in message_data:

            if item["emoji"] != emoji:
                continue

            role = guild.get_role(
                item["role_id"]
            )

            if role:
                try:
                    await member.remove_roles(role)
                except discord.HTTPException:
                    pass


async def setup(bot):
    await bot.add_cog(ReactionRoles(bot))