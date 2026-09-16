import discord
from discord import app_commands
from discord.ext import commands

from config import TICKET_FILE
from utils.storage import load_json


# ── fixed setup ───────────────────────────────────────────────

REVIEW_THREAD_ID = 1547416735072915546

BUTTERFLY = "<:4butterfly:1547846639312699473>"
LEFT_WING = "<a:xwingleft:1549545518512865373>"
RIGHT_WING = "<a:xwingright:1549545512309624912>"
KAMOJIS = "<:kamojis:1549545521960714270>"

GIF_URL = (
    "https://cdn.discordapp.com/attachments/"
    "1535240915428315196/1535272337228832848/"
    "GIF_image_8.gif?ex=6aaa93c9&is=6aa94249&"
    "hm=fdafe8b105ffccf87e9ba1bd979cb8368a7e403563a15db0a20a1b2599134bb3&"
)


# ── helpers ───────────────────────────────────────────────────

def has_completed_hire(user_id: int):
    data = load_json(
        TICKET_FILE,
        {
            "tickets": {},
            "mass_completed": {},
            "hire_completed": {},
        },
    )

    hire_completed = data.get(
        "hire_completed",
        {},
    )

    return bool(
        hire_completed.get(str(user_id), False)
    )


# ── review modal ──────────────────────────────────────────────

class ReviewModal(discord.ui.Modal):

    def __init__(self):
        super().__init__(
            title="Mia review"
        )

        self.plan = discord.ui.TextInput(
            label="plan",
            placeholder="which plan did you hire Mia for?",
            required=True,
            max_length=100,
        )

        self.rate = discord.ui.TextInput(
            label="rate",
            placeholder="rate Mia's services",
            required=True,
            max_length=50,
        )

        self.thoughts = discord.ui.TextInput(
            label="thoughts",
            placeholder="optional additional thoughts",
            required=False,
            style=discord.TextStyle.paragraph,
            max_length=1000,
        )

        self.add_item(self.plan)
        self.add_item(self.rate)
        self.add_item(self.thoughts)

    async def on_submit(
        self,
        interaction: discord.Interaction,
    ):
        thread = interaction.client.get_channel(
            REVIEW_THREAD_ID
        )

        if thread is None:

            try:
                thread = await interaction.client.fetch_channel(
                    REVIEW_THREAD_ID
                )
            except (
                discord.NotFound,
                discord.Forbidden,
                discord.HTTPException,
            ):
                await interaction.response.send_message(
                    "I couldn't find the review thread.",
                    ephemeral=True,
                )
                return

        if not isinstance(
            thread,
            discord.Thread,
        ):
            await interaction.response.send_message(
                "The review destination isn't a thread.",
                ephemeral=True,
            )
            return

        plan = self.plan.value.strip()
        rate = self.rate.value.strip()
        thoughts = self.thoughts.value.strip()

        if thoughts:
            thoughts_line = (
                f"-# thoughts⠀{KAMOJIS}  ー   {thoughts}"
            )
        else:
            thoughts_line = (
                f"-# thoughts⠀{KAMOJIS}  ー   n/a"
            )

        review_message = (
            "_ _\n"
            f"{LEFT_WING} {RIGHT_WING} ⠀ "
            f"[﹒]({GIF_URL}) ⠀ "
            f"{interaction.user.name}‘s review\n"
            f"plan: ⠀ {plan}\n"
            f"rate: ⠀ {rate}\n\n"
            f"{thoughts_line}\n"
            "_ _"
        )

        try:

            await thread.send(
                review_message
            )

        except discord.Forbidden:

            await interaction.response.send_message(
                "I don't have permission to send reviews there.",
                ephemeral=True,
            )
            return

        except discord.HTTPException as error:

            print(
                f"Review send error: "
                f"{type(error).__name__}: {error}"
            )

            await interaction.response.send_message(
                "Discord rejected the review.",
                ephemeral=True,
            )
            return

        await interaction.response.send_message(
            "♡ your review has been sent.",
            ephemeral=True,
        )


# ── reviews cog ───────────────────────────────────────────────

class Reviews(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(
        name="rev",
        description="Leave a review for Mia.",
    )
    async def rev(
        self,
        interaction: discord.Interaction,
    ):

        # ── DM only ──────────────────────────────────────

        if interaction.guild is not None:

            await interaction.response.send_message(
                "♡ `/rev` can only be used in DMs.",
                ephemeral=True,
            )
            return

        # ── completed Hire required ──────────────────────

        if not has_completed_hire(
            interaction.user.id
        ):

            await interaction.response.send_message(
                "♡ you can only leave a review after "
                "completing a Hire ticket.",
                ephemeral=True,
            )
            return

        await interaction.response.send_modal(
            ReviewModal()
        )


async def setup(bot):
    await bot.add_cog(
        Reviews(bot)
    )