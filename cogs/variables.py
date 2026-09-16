import discord
from discord import app_commands
from discord.ext import commands


class Variables(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(
        name="variables",
        description="Display every available customization variable."
    )
    async def variables(self, interaction: discord.Interaction):

        embed = discord.Embed(
            title="✧ available variables",
            description=(
                "Use these inside customizable messages, embeds, "
                "channel names, ticket names, etc.\n\n"
                "── ୨୧ ・⸝⸝"
            ),
            color=0x2B2028,
        )

        embed.add_field(
            name="♡ User",
            value=(
                "`{user}`\n"
                "`{user_mention}`\n"
                "`{user_name}`\n"
                "`{user_display_name}`\n"
                "`{user_id}`\n"
                "`{user_avatar}`"
            ),
            inline=True,
        )

        embed.add_field(
            name="🎀 Member",
            value=(
                "`{member}`\n"
                "`{member_name}`\n"
                "`{member_display_name}`\n"
                "`{member_id}`\n"
                "`{member_avatar}`\n"
                "`{member_joined_at}`"
            ),
            inline=True,
        )

        embed.add_field(
            name="☾ Server",
            value=(
                "`{server}`\n"
                "`{server_name}`\n"
                "`{server_id}`\n"
                "`{server_avatar}`\n"
                "`{server_owner}`\n"
                "`{server_member_count}`"
            ),
            inline=True,
        )

        embed.add_field(
            name="✧ Channel",
            value=(
                "`{channel}`\n"
                "`{channel_name}`\n"
                "`{channel_id}`\n"
                "`{channel_category}`"
            ),
            inline=True,
        )

        embed.add_field(
            name="⋆ Message",
            value=(
                "`{message_id}`\n"
                "`{message_content}`\n"
                "`{message_url}`"
            ),
            inline=True,
        )

        embed.add_field(
            name="𓂃 Time",
            value=(
                "`{time}`\n"
                "`{time_12}`\n"
                "`{date}`\n"
                "`{datetime}`\n"
                "`{year}`\n"
                "`{month}`\n"
                "`{day}`"
            ),
            inline=True,
        )

        await interaction.response.send_message(
            embed=embed,
            ephemeral=True,
        )


async def setup(bot):
    await bot.add_cog(Variables(bot))