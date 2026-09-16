from datetime import timedelta
import discord
from discord import app_commands
from discord.ext import commands


class Moderation(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(
        name="ban",
        description="Ban a member."
    )
    @app_commands.checks.has_permissions(ban_members=True)
    async def ban(
        self,
        interaction: discord.Interaction,
        member: discord.Member,
        reason: str = "No reason provided.",
    ):

        await member.ban(reason=reason)

        await interaction.response.send_message(
            f"♡ {member.mention} has been banned.\n"
            f"Reason: {reason}"
        )

    @app_commands.command(
        name="kick",
        description="Kick a member."
    )
    @app_commands.checks.has_permissions(kick_members=True)
    async def kick(
        self,
        interaction: discord.Interaction,
        member: discord.Member,
        reason: str = "No reason provided.",
    ):

        await member.kick(reason=reason)

        await interaction.response.send_message(
            f"♡ {member.mention} has been kicked.\n"
            f"Reason: {reason}"
        )

    @app_commands.command(
        name="timeout",
        description="Timeout a member."
    )
    @app_commands.checks.has_permissions(moderate_members=True)
    async def timeout(
        self,
        interaction: discord.Interaction,
        member: discord.Member,
        minutes: app_commands.Range[int, 1, 40320],
        reason: str = "No reason provided.",
    ):

        duration = discord.utils.utcnow() + timedelta(
            minutes=minutes
        )

        await member.timeout(
            discord.utils.utcnow()
            + timedelta(minutes=minutes),
            reason=reason,
        )

        await interaction.response.send_message(
            f"♡ {member.mention} has been timed out for "
            f"{minutes} minute(s)."
        )

    @app_commands.command(
        name="purge",
        description="Delete recent messages."
    )
    @app_commands.checks.has_permissions(
        manage_messages=True
    )
    async def purge(
        self,
        interaction: discord.Interaction,
        amount: app_commands.Range[int, 1, 100],
    ):

        await interaction.response.defer(
            ephemeral=True
        )

        deleted = await interaction.channel.purge(
            limit=amount
        )

        await interaction.followup.send(
            f"✧ deleted {len(deleted)} message(s).",
            ephemeral=True,
        )

    @app_commands.command(
        name="lock",
        description="Lock the current channel."
    )
    @app_commands.checks.has_permissions(
        manage_channels=True
    )
    async def lock(
        self,
        interaction: discord.Interaction,
    ):

        overwrite = interaction.channel.overwrites_for(
            interaction.guild.default_role
        )

        overwrite.send_messages = False

        await interaction.channel.set_permissions(
            interaction.guild.default_role,
            overwrite=overwrite,
        )

        await interaction.response.send_message(
            "☾ this channel is now locked."
        )

    @app_commands.command(
        name="rename",
        description="Rename a channel."
    )
    @app_commands.checks.has_permissions(
        manage_channels=True
    )
    async def rename(
        self,
        interaction: discord.Interaction,
        name: str,
    ):

        await interaction.channel.edit(name=name)

        await interaction.response.send_message(
            f"✧ channel renamed to `{name}`."
        )


async def setup(bot):
    await bot.add_cog(Moderation(bot))