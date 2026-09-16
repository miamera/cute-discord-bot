import discord
from discord.ext import commands

from config import CONFIG_FILE
from utils.storage import load_json, save_json


class Logs(commands.Cog):

    def __init__(self, bot):
        self.bot = bot
        self.config = load_json(CONFIG_FILE, {})

    async def send_log(
        self,
        guild: discord.Guild,
        *,
        title: str,
        description: str,
        color: int = 0x2B2028,
    ):

        settings = self.config.get(str(guild.id), {})
        channel_id = settings.get("log_channel_id")

        if not channel_id:
            return

        channel = guild.get_channel(channel_id)

        if not channel:
            return

        embed = discord.Embed(
            title=f"✧ {title}",
            description=description,
            color=color,
            timestamp=discord.utils.utcnow(),
        )

        try:
            await channel.send(embed=embed)
        except discord.HTTPException:
            pass

    @commands.Cog.listener()
    async def on_message_delete(self, message):

        if not message.guild or message.author.bot:
            return

        await self.send_log(
            message.guild,
            title="message deleted",
            description=(
                f"**author:** {message.author.mention}\n"
                f"**channel:** {message.channel.mention}\n"
                f"**content:** {message.content[:1000]}"
            ),
        )

    @commands.Cog.listener()
    async def on_member_join(self, member):

        await self.send_log(
            member.guild,
            title="member joined",
            description=(
                f"{member.mention} joined the server."
            ),
        )

    @commands.Cog.listener()
    async def on_member_remove(self, member):

        await self.send_log(
            member.guild,
            title="member left",
            description=(
                f"**member:** {member}\n"
                f"**id:** `{member.id}`"
            ),
        )

    @discord.app_commands.command(
        name="setlogs",
        description="Set the server's log channel."
    )
    @discord.app_commands.checks.has_permissions(
        manage_guild=True
    )
    async def setlogs(
        self,
        interaction: discord.Interaction,
        channel: discord.TextChannel,
    ):

        guild_id = str(interaction.guild.id)

        if guild_id not in self.config:
            self.config[guild_id] = {}

        self.config[guild_id]["log_channel_id"] = channel.id

        save_json(CONFIG_FILE, self.config)

        await interaction.response.send_message(
            f"✧ logs will now be sent to {channel.mention}.",
            ephemeral=True,
        )


async def setup(bot):
    await bot.add_cog(Logs(bot))