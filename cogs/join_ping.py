import discord
from discord.ext import commands


JOIN_CHANNEL_ID = 1546721710466666577


class JoinPing(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member):

        channel = member.guild.get_channel(
            JOIN_CHANNEL_ID
        )

        if channel is None:
            try:
                channel = await member.guild.fetch_channel(
                    JOIN_CHANNEL_ID
                )
            except (
                discord.NotFound,
                discord.Forbidden,
                discord.HTTPException,
            ):
                return

        if not isinstance(
            channel,
            discord.TextChannel,
        ):
            return

        try:
            message = await channel.send(
                member.mention
            )

            await message.delete()

        except (
            discord.Forbidden,
            discord.HTTPException,
        ):
            return


async def setup(bot):
    await bot.add_cog(JoinPing(bot))