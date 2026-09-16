import discord
from discord import app_commands
from discord.ext import commands


class Help(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(
        name="help",
        description="View everything the bot can do."
    )
    async def help_command(self, interaction: discord.Interaction):

        embed = discord.Embed(
            title="୨୧  bot help",
            description=(
                "── ୨୧ ・⸝⸝\n"
                "A clean little list of everything available."
            ),
            color=0x2B2028,
        )

        embed.add_field(
            name="🎀 Tickets",
            value=(
                "`/ticket panel`\n"
                "Create customizable ticket panels.\n"
                "Buttons • menus • reactions • transcripts"
            ),
            inline=False,
        )

        embed.add_field(
            name="♡ Auto Responders",
            value=(
                "`/autoresponder`\n"
                "Messages • reactions • names • channels • embeds"
            ),
            inline=False,
        )

        embed.add_field(
            name="✧ Join Ping",
            value=(
                "`/joinping`\n"
                "Configure a customizable member-join message."
            ),
            inline=False,
        )

        embed.add_field(
            name="୨୧ Reaction Roles",
            value=(
                "`/reactionrole`\n"
                "Buttons • reactions • select menus"
            ),
            inline=False,
        )

        embed.add_field(
            name="☾ Moderation",
            value=(
                "`/ban`\n"
                "`/kick`\n"
                "`/timeout`\n"
                "`/purge`\n"
                "`/lock`\n"
                "`/rename`"
            ),
            inline=False,
        )

        embed.add_field(
            name="⋆ Utilities",
            value=(
                "`/variables` — available variables\n"
                "`/help` — this menu"
            ),
            inline=False,
        )

        embed.set_footer(
            text="♡ clean • customizable • cute"
        )

        await interaction.response.send_message(
            embed=embed,
            ephemeral=True,
        )


async def setup(bot):
    await bot.add_cog(Help(bot))