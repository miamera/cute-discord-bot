import discord
from discord import app_commands
from discord.ext import commands
from datetime import datetime, timezone, timedelta

from config import TICKET_FILE
from utils.storage import load_json, save_json


# ── fixed setup ───────────────────────────────────────────────

REVIEW_THREAD_ID = 1547416735072915546
MASS_REVIEW_THREAD_ID = 1547416623063760976
MASS_REVIEW_WINDOW = timedelta(hours=24)

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

def get_ticket_data():
    return load_json(
        TICKET_FILE,
        {
            "tickets": {},
            "mass_completed": {},
            "hire_completed": {},
            "mass_reviews": {},
        },
    )


def has_completed_hire(user_id: int):
    data = get_ticket_data()
    return bool(
        data.get("hire_completed", {}).get(str(user_id), False)
    )


def get_mass_review_entry(user_id: int):
    data = get_ticket_data()
    entries = data.get("mass_reviews", {}).get(str(user_id), [])
    now = datetime.now(timezone.utc)

    changed = False
    available = None
    has_expired_unused = False

    for entry in entries:
        if entry.get("used"):
            continue

        try:
            completed_at = datetime.fromisoformat(
                entry.get("completed_at", "")
            )
            if completed_at.tzinfo is None:
                completed_at = completed_at.replace(tzinfo=timezone.utc)
        except (TypeError, ValueError):
            continue

        if now - completed_at <= MASS_REVIEW_WINDOW:
            available = entry
            break

        has_expired_unused = True

    return data, available, has_expired_unused


async def get_review_thread(client, thread_id: int):
    thread = client.get_channel(thread_id)

    if thread is None:
        try:
            thread = await client.fetch_channel(thread_id)
        except (discord.NotFound, discord.Forbidden, discord.HTTPException):
            return None

    if not isinstance(thread, discord.Thread):
        return None

    return thread


# ── Hire review modal ─────────────────────────────────────────

class ReviewModal(discord.ui.Modal):

    def __init__(self):
        super().__init__(title="Mia review")

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

    async def on_submit(self, interaction: discord.Interaction):
        thread = await get_review_thread(
            interaction.client,
            REVIEW_THREAD_ID,
        )

        if thread is None:
            await interaction.response.send_message(
                "I couldn't find the review thread.",
                ephemeral=True,
            )
            return

        plan = self.plan.value.strip()
        rate = self.rate.value.strip()
        thoughts = self.thoughts.value.strip()

        thoughts_line = (
            f"-# thoughts⠀{KAMOJIS}  ー   {thoughts}"
            if thoughts
            else f"-# thoughts⠀{KAMOJIS}  ー   n/a"
        )

        review_message = (
            "_ _\n"
            f"{LEFT_WING} {RIGHT_WING} ⠀ [﹒]({GIF_URL}) ⠀ "
            f"{interaction.user.name}‘s review\n"
            f"plan: ⠀ {plan}\n"
            f"rate: ⠀ {rate}\n\n"
            f"{thoughts_line}\n"
            "_ _"
        )

        try:
            await thread.send(review_message)
        except discord.Forbidden:
            await interaction.response.send_message(
                "I don't have permission to send reviews there.",
                ephemeral=True,
            )
            return
        except discord.HTTPException as error:
            print(f"Review send error: {type(error).__name__}: {error}")
            await interaction.response.send_message(
                "Discord rejected the review.",
                ephemeral=True,
            )
            return

        await interaction.response.send_message(
            "♡ your review has been sent.",
            ephemeral=True,
        )


# ── Mass review modal ─────────────────────────────────────────

class MassReviewModal(discord.ui.Modal):

    def __init__(self, review_entry):
        super().__init__(title="Mia mass review")
        self.review_entry = review_entry

        self.sep = discord.ui.TextInput(
            label="sep",
            placeholder="how was the sep?",
            required=True,
            max_length=1000,
        )

        self.invs = discord.ui.TextInput(
            label="invs",
            placeholder="how were the invs?",
            required=True,
            max_length=1000,
        )

        self.thoughts = discord.ui.TextInput(
            label="thoughts",
            placeholder="optional additional thoughts",
            required=False,
            style=discord.TextStyle.paragraph,
            max_length=1000,
        )

        self.add_item(self.sep)
        self.add_item(self.invs)
        self.add_item(self.thoughts)

    async def on_submit(self, interaction: discord.Interaction):
        data = get_ticket_data()
        user_entries = data.setdefault("mass_reviews", {}).setdefault(
            str(interaction.user.id), []
        )

        target = None
        for entry in user_entries:
            if entry is self.review_entry:
                target = entry
                break

        if target is None or target.get("used"):
            await interaction.response.send_message(
                "♡ this Mass review has already been used.",
                ephemeral=True,
            )
            return

        try:
            completed_at = datetime.fromisoformat(
                target.get("completed_at", "")
            )
            if completed_at.tzinfo is None:
                completed_at = completed_at.replace(tzinfo=timezone.utc)
        except (TypeError, ValueError):
            await interaction.response.send_message(
                "♡ this review window is no longer available.",
                ephemeral=True,
            )
            return

        if datetime.now(timezone.utc) - completed_at > MASS_REVIEW_WINDOW:
            await interaction.response.send_message(
                "-# ♡ the window to review has ended. thnk u",
                ephemeral=True,
            )
            return

        thread = await get_review_thread(
            interaction.client,
            MASS_REVIEW_THREAD_ID,
        )

        if thread is None:
            await interaction.response.send_message(
                "I couldn't find the Mass review thread.",
                ephemeral=True,
            )
            return

        sep = self.sep.value.strip()
        invs = self.invs.value.strip()
        thoughts = self.thoughts.value.strip()

        thoughts_line = (
            f"-# thoughts⠀{KAMOJIS}  ー   {thoughts}"
            if thoughts
            else f"-# thoughts⠀{KAMOJIS}  ー   n/a"
        )

        review_message = (
            "_ _\n"
            f"{LEFT_WING} {RIGHT_WING} ⠀ [﹒]({GIF_URL}) ⠀ "
            f"{interaction.user.name}’s review\n"
            f"sep: ⠀ {sep}\n"
            f"invs: ⠀ {invs}\n\n"
            f"{thoughts_line}\n"
            "_ _"
        )

        try:
            await thread.send(review_message)
        except discord.Forbidden:
            await interaction.response.send_message(
                "I don't have permission to send reviews there.",
                ephemeral=True,
            )
            return
        except discord.HTTPException as error:
            print(f"Mass review send error: {type(error).__name__}: {error}")
            await interaction.response.send_message(
                "Discord rejected the review.",
                ephemeral=True,
            )
            return

        target["used"] = True
        save_json(TICKET_FILE, data)

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
    async def rev(self, interaction: discord.Interaction):
        if interaction.guild is not None:
            await interaction.response.send_message(
                "♡ `/rev` can only be used in DMs.",
                ephemeral=True,
            )
            return

        if not has_completed_hire(interaction.user.id):
            await interaction.response.send_message(
                "♡ you can only leave a review after completing a Hire ticket.",
                ephemeral=True,
            )
            return

        await interaction.response.send_modal(ReviewModal())

    @app_commands.command(
        name="mrev",
        description="Leave a review for a recently completed Mass.",
    )
    async def mrev(self, interaction: discord.Interaction):
        if interaction.guild is not None:
            await interaction.response.send_message(
                "♡ `/mrev` can only be used in DMs.",
                ephemeral=True,
            )
            return

        data, entry, has_expired_unused = get_mass_review_entry(
            interaction.user.id
        )

        if entry is None:
            if has_expired_unused:
                message = "-# ♡ the window to review has ended. thnk u"
            else:
                message = "♡ you don't have a recently completed Mass available to review."

            await interaction.response.send_message(
                message,
                ephemeral=True,
            )
            return

        await interaction.response.send_modal(
            MassReviewModal(entry)
        )


async def setup(bot):
    await bot.add_cog(Reviews(bot))
