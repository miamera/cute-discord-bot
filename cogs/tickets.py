import io
import re
from datetime import datetime, timezone

import discord
from discord import app_commands
from discord.ext import commands

from config import TICKET_FILE
from utils.storage import load_json, save_json


# ── fixed setup ───────────────────────────────────────────────

PANEL_CHANNEL_ID = 1547417248946454599
TICKET_CATEGORY_ID = 1549007825198387312
TRANSCRIPT_CHANNEL_ID = 1548952234790883399

MAX_TICKETS_PER_TYPE = 3

SPARK = "<a:00_spark:1547846651790626907>"

BUTTERFLY = "<:4butterfly:1547846639312699473>"

MASS_EMOJI = "<:4butterfly:1547846639312699473>"
HIRE_EMOJI = "<:4butterfly:1547846639312699473>"

MASS_OPENING = "` .mass ` <:kamojis:1549545521960714270>"
HIRE_OPENING = "` .hire ` <:kamojis:1549545521960714270>"


# ── panel images ──────────────────────────────────────────────

IMAGE_ONE = (
    "[──ִ──ׁ──ִ──ׁ─ ´ཀ` ─ׅ──ׁ──ׅ──ׁ──ׅ━]"
    "(https://cdn.discordapp.com/attachments/"
    "1544685429759025263/1549513431978090617/"
    "IMG_6410.jpg?ex=6aaaf856&is=6aa9a6d6&"
    "hm=3759cb417b3c2da3f1e54f86cae106569b2f9c78f4612ffd7633516ba9a6de87&)"
)

IMAGE_TWO = (
    "[──ִ──ׁ──ִ──ׁ─ ´ཀ` ─ׅ──ׁ──ׅ──ׁ──ׅ━]"
    "(https://cdn.discordapp.com/attachments/"
    "1535240915428315196/1535272337228832848/"
    "GIF_image_8.gif?ex=6aaa93c9&is=6aa94249&"
    "hm=fdafe8b105ffccf87e9ba1bd979cb8368a7e403563a15db0a20a1b2599134bb3&)"
)


# ── info messages ─────────────────────────────────────────────

HIRE_INFO = """_ _

-# ptb: ⠀ any server
-# invb: ⠀20mc ⠀scl stox ⠀shrt ad
♡ ﹒  ◡◡
-# ` $1 `⠀  500  pt / 50i 
-# ` $3 `⠀  1.0k  pt / 110i
-# ` $5 `⠀  2.2k pt / 175i
-# ` $10 `⠀3.5k pt / 350i


_ _"""


MASS_INFO = """_ _ ⠀⠀⠀⠀⠀ ⠀⠀ ⠀⠀⠀⠀ ⠀⠀⠀⠀⠀ ⠀  ⠀ ⠀

-# ⠀⠀⠀⠀ ⠀⠀⠀⠀⠀⠀ ⠀⠀⠀⠀⠀anytox ⠀ sfw ⠀anymc ⠀no adv
⠀⠀⠀⠀ ⠀⠀⠀⠀⠀⠀ ⠀⠀⠀⠀  ⠀  ⠀⠀⠀ ⠀  ⠀    ⠀ ◡◡  ﹒ ♡
-# ⠀⠀⠀⠀     ⠀ ⠀ ⠀⠀⠀⠀⠀⠀ ⠀⠀⠀⠀ batch ⠀2h ⠀5h  ⠀` avb `
-# ⠀⠀⠀⠀     ⠀   ⠀ ⠀ ⠀⠀⠀⠀⠀⠀ ⠀  10h ⠀20h⠀30h  ⠀` earn `


_ _"""


# ── ticket storage ────────────────────────────────────────────

def load_ticket_data():
    data = load_json(
        TICKET_FILE,
        {
            "tickets": {},
            "mass_completed": {},
            "hire_completed": {},
        },
    )

    if "tickets" not in data:
        data["tickets"] = {}

    if "mass_completed" not in data:
        data["mass_completed"] = {}

    if "hire_completed" not in data:
        data["hire_completed"] = {}

    return data


def save_ticket_data(data):
    save_json(TICKET_FILE, data)


# ── helpers ───────────────────────────────────────────────────

def get_ticket_record(channel_id: int):
    data = load_ticket_data()
    return data["tickets"].get(str(channel_id))


def clean_ticket_records(guild: discord.Guild):
    data = load_ticket_data()
    changed = False

    for channel_id in list(data["tickets"].keys()):

        record = data["tickets"][channel_id]

        if str(record.get("guild_id")) != str(guild.id):
            continue

        if guild.get_channel(int(channel_id)) is None:
            del data["tickets"][channel_id]
            changed = True

    if changed:
        save_ticket_data(data)

    return data


def get_ticket_type_from_name(channel_name: str):
    if channel_name.startswith("m "):
        return "mass"

    if channel_name.startswith("h "):
        return "hire"

    if channel_name.startswith("m𑣲"):
        return "mass"

    if channel_name.startswith("h𑣲"):
        return "hire"

    return None


async def find_ticket_opener(
    channel: discord.TextChannel,
    guild: discord.Guild,
):
    record = get_ticket_record(channel.id)

    if record:
        user_id = record.get("user_id")

        if user_id:
            member = guild.get_member(int(user_id))

            if member:
                return member

            try:
                return await guild.fetch_member(int(user_id))
            except (discord.NotFound, discord.HTTPException):
                pass

    for target, overwrite in channel.overwrites.items():

        if not isinstance(target, discord.Member):
            continue

        if guild.me and target.id == guild.me.id:
            continue

        if overwrite.view_channel is True:
            return target

    return None


def build_transcript_text(messages):
    lines = []

    for message in messages:

        timestamp = message.created_at.astimezone(
            timezone.utc
        ).strftime("%Y-%m-%d %H:%M:%S UTC")

        author = message.author

        if isinstance(author, discord.Member):
            author_name = author.name
        else:
            author_name = getattr(
                author,
                "name",
                str(author),
            )

        content = message.content.strip()

        if content:
            lines.append(
                f"[{timestamp}] {author_name}: {content}"
            )
        else:
            lines.append(
                f"[{timestamp}] {author_name}: (no text)"
            )

        for attachment in message.attachments:
            lines.append(
                f"    Attachment: {attachment.url}"
            )

        for embed in message.embeds:

            embed_parts = []

            if embed.title:
                embed_parts.append(
                    f"Title: {embed.title}"
                )

            if embed.description:
                embed_parts.append(
                    f"Description: {embed.description}"
                )

            if embed.url:
                embed_parts.append(
                    f"URL: {embed.url}"
                )

            if embed_parts:
                lines.append(
                    f"    Embed — {' | '.join(embed_parts)}"
                )

        if message.edited_at:
            lines.append(
                f"    Edited: "
                f"{message.edited_at.astimezone(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}"
            )

    if not lines:
        return "(No messages found.)"

    return "\n".join(lines)


def safe_filename(name: str):
    name = re.sub(
        r"[^a-zA-Z0-9._-]+",
        "-",
        name,
    )

    return name[:80] or "ticket"


# ── close ticket button ───────────────────────────────────────

class CloseTicketView(discord.ui.View):

    def __init__(self, cog=None):
        super().__init__(timeout=None)
        self.cog = cog

    @discord.ui.button(
        label="c",
        style=discord.ButtonStyle.secondary,
        custom_id="ticket_close",
    )
    async def close_ticket(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button,
    ):
        channel = interaction.channel

        if not isinstance(channel, discord.TextChannel):
            await interaction.response.send_message(
                f"{SPARK} this isn't a ticket channel.",
                ephemeral=True,
            )
            return

        guild = interaction.guild

        if guild is None:
            await interaction.response.send_message(
                f"{SPARK} this isn't inside a server.",
                ephemeral=True,
            )
            return

        record = get_ticket_record(channel.id)

        opener = await find_ticket_opener(
            channel,
            guild,
        )

        # ── closing permissions ──────────────────────────

        is_opener = (
            opener is not None
            and interaction.user.id == opener.id
        )

        is_staff = (
            isinstance(
                interaction.user,
                discord.Member,
            )
            and interaction.user.guild_permissions.manage_channels
        )

        if not is_opener and not is_staff:

            await interaction.response.send_message(
                f"{SPARK} only the ticket opener or staff "
                "can close this ticket.",
                ephemeral=True,
            )
            return

        await interaction.response.defer(
            ephemeral=True
        )

        ticket_name = channel.name

        if record:
            ticket_type = record.get("ticket_type")
        else:
            ticket_type = get_ticket_type_from_name(
                channel.name
            )

        if ticket_type not in ("mass", "hire"):
            ticket_type = "hire"

        # ── fetch full transcript ─────────────────────────

        try:

            messages = [
                message
                async for message in channel.history(
                    limit=None,
                    oldest_first=True,
                )
            ]

            transcript_text = build_transcript_text(
                messages
            )

        except discord.HTTPException as error:

            print(
                f"Transcript fetch error: "
                f"{type(error).__name__}: {error}"
            )

            transcript_text = (
                "Unable to retrieve the full ticket history."
            )

        # ── transcript channel ───────────────────────────

        transcript_channel = guild.get_channel(
            TRANSCRIPT_CHANNEL_ID
        )

        transcript_sent = False

        if isinstance(
            transcript_channel,
            discord.TextChannel,
        ):

            opener_text = (
                opener.mention
                if opener
                else "Unknown"
            )

            closer_text = interaction.user.mention

            header = (
                f"{BUTTERFLY}  **Ticket Transcript**\n"
                f"Ticket: {ticket_name}\n"
                f"Opened by: {opener_text}\n"
                f"Closed by: {closer_text}"
            )

            transcript_file = discord.File(
                io.BytesIO(
                    transcript_text.encode(
                        "utf-8"
                    )
                ),
                filename=(
                    f"{safe_filename(ticket_name)}.txt"
                ),
            )

            try:

                await transcript_channel.send(
                    content=header,
                    file=transcript_file,
                )

                transcript_sent = True

            except discord.HTTPException as error:

                print(
                    f"Transcript send error: "
                    f"{type(error).__name__}: {error}"
                )

        else:

            print(
                "Transcript channel could not be found."
            )

        # ── completion tracking / DM ──────────────────────

        dm_sent = False

        if opener:

            data = load_ticket_data()
            user_key = str(opener.id)

            if ticket_type == "mass":

                completed = int(
                    data["mass_completed"].get(
                        user_key,
                        0,
                    )
                )

                completed += 1

                data["mass_completed"][user_key] = (
                    completed
                )

                save_ticket_data(data)

                level = min(
                    completed,
                    5,
                )

                dm_message = (
                    f"{BUTTERFLY}  **Ty for massing w/ Mia**\n"
                    f"-# You’re {level}/5 masses away "
                    f"from unlocking earned seps"
                )

            else:

                # A Hire ticket only unlocks /rev AFTER
                # its transcript was successfully saved.
                if transcript_sent:

                    data["hire_completed"][user_key] = True

                    save_ticket_data(data)

                dm_message = (
                    f"{BUTTERFLY}  **Ty for hiring Mia**\n"
                    f"-# If you’d like to leave a review "
                    f"please use ` /rev ` here"
                )

            try:

                await opener.send(
                    dm_message
                )

                dm_sent = True

            except discord.Forbidden:

                print(
                    f"Could not DM ticket opener "
                    f"{opener} — DMs are closed."
                )

            except discord.HTTPException as error:

                print(
                    f"Ticket opener DM error: "
                    f"{type(error).__name__}: {error}"
                )

        # ── delete ticket ────────────────────────────────

        try:

            await channel.delete(
                reason=(
                    f"Ticket closed by "
                    f"{interaction.user}"
                ),
            )

        except discord.Forbidden:

            await interaction.followup.send(
                f"{SPARK} I don't have permission "
                "to delete this ticket.",
                ephemeral=True,
            )
            return

        except discord.HTTPException as error:

            print(
                f"Ticket delete error: "
                f"{type(error).__name__}: {error}"
            )

            await interaction.followup.send(
                f"{SPARK} Discord rejected the ticket deletion.",
                ephemeral=True,
            )
            return

        # ── remove active ticket record ──────────────────

        data = load_ticket_data()

        data["tickets"].pop(
            str(channel.id),
            None,
        )

        save_ticket_data(data)

        status = []

        if transcript_sent:
            status.append("transcript saved")

        if dm_sent:
            status.append("DM sent")

        status_text = (
            " • ".join(status)
            if status
            else "ticket closed"
        )

        try:

            await interaction.followup.send(
                f"{SPARK} {status_text}.",
                ephemeral=True,
            )

        except discord.HTTPException:
            pass


# ── ticket select menu ────────────────────────────────────────

class TicketSelect(discord.ui.Select):

    def __init__(self, cog):
        self.cog = cog

        options = [
            discord.SelectOption(
                label="𖥻 mass ! ﹒",
                value="mass",
                emoji=discord.PartialEmoji.from_str(
                    MASS_EMOJI
                ),
            ),
            discord.SelectOption(
                label="𖥻 hire ! ﹒",
                value="hire",
                emoji=discord.PartialEmoji.from_str(
                    HIRE_EMOJI
                ),
            ),
        ]

        super().__init__(
            placeholder="ticket select",
            min_values=1,
            max_values=1,
            options=options,
            custom_id="ticket_type_select",
        )

    async def callback(
        self,
        interaction: discord.Interaction,
    ):
        ticket_type = self.values[0]

        await self.cog.create_ticket(
            interaction,
            ticket_type,
        )


class TicketSelectView(discord.ui.View):

    def __init__(self, cog):
        super().__init__(timeout=None)

        self.add_item(
            TicketSelect(cog)
        )


# ── information buttons ──────────────────────────────────────

class InfoButtonsView(discord.ui.View):

    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(
        emoji="<a:xwingleft:1549545518512865373>",
        style=discord.ButtonStyle.secondary,
        custom_id="ticket_hire_info",
    )
    async def hire_info(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button,
    ):
        await interaction.response.send_message(
            HIRE_INFO,
            ephemeral=True,
        )

    @discord.ui.button(
        emoji="<a:xwingright:1549545512309624912>",
        style=discord.ButtonStyle.secondary,
        custom_id="ticket_mass_info",
    )
    async def mass_info(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button,
    ):
        await interaction.response.send_message(
            MASS_INFO,
            ephemeral=True,
        )


# ── tickets cog ───────────────────────────────────────────────

class Tickets(commands.Cog):

    def __init__(self, bot):
        self.bot = bot

    async def cog_load(self):

        self.bot.add_view(
            TicketSelectView(self)
        )

        self.bot.add_view(
            InfoButtonsView()
        )

        self.bot.add_view(
            CloseTicketView(self)
        )

    # ── /mia ──────────────────────────────────────────────────

    @app_commands.command(
        name="mia",
        description="Send the ticket panel.",
    )
    @app_commands.checks.has_permissions(
        manage_channels=True,
    )
    async def mia(
        self,
        interaction: discord.Interaction,
    ):
        await interaction.response.defer(
            ephemeral=True
        )

        channel = interaction.guild.get_channel(
            PANEL_CHANNEL_ID
        )

        if channel is None:
            await interaction.followup.send(
                f"{SPARK} I couldn't find the ticket panel channel.",
                ephemeral=True,
            )
            return

        try:

            await channel.send(
                IMAGE_ONE
            )

            await channel.send(
                view=TicketSelectView(self)
            )

            await channel.send(
                IMAGE_TWO
            )

            await channel.send(
                view=InfoButtonsView()
            )

            await interaction.followup.send(
                f"{SPARK} the ticket panel has been sent.",
                ephemeral=True,
            )

            print(
                f"Ticket panel sent to #{channel.name}"
            )

        except discord.Forbidden:

            await interaction.followup.send(
                f"{SPARK} I don't have permission "
                "to send messages there.",
                ephemeral=True,
            )

        except discord.HTTPException as error:

            print(
                f"Ticket panel error: "
                f"{type(error).__name__}: {error}"
            )

            await interaction.followup.send(
                f"{SPARK} Discord rejected the panel.",
                ephemeral=True,
            )

        except Exception as error:

            print(
                f"Ticket panel error: "
                f"{type(error).__name__}: {error}"
            )

            await interaction.followup.send(
                f"{SPARK} something went wrong.",
                ephemeral=True,
            )

    # ── create ticket ─────────────────────────────────────────

    async def create_ticket(
        self,
        interaction: discord.Interaction,
        ticket_type: str,
    ):

        guild = interaction.guild
        member = interaction.user

        if guild is None:
            await interaction.response.send_message(
                f"{SPARK} tickets can only be opened inside a server.",
                ephemeral=True,
            )
            return

        if not isinstance(member, discord.Member):
            await interaction.response.send_message(
                f"{SPARK} I couldn't find your server membership.",
                ephemeral=True,
            )
            return

        category = guild.get_channel(
            TICKET_CATEGORY_ID
        )

        if not isinstance(
            category,
            discord.CategoryChannel,
        ):
            await interaction.response.send_message(
                f"{SPARK} I couldn't find the ticket category.",
                ephemeral=True,
            )
            return

        if ticket_type not in ("mass", "hire"):
            await interaction.response.send_message(
                f"{SPARK} invalid ticket type.",
                ephemeral=True,
            )
            return

        data = clean_ticket_records(guild)

        existing_tickets = 0

        for record in data["tickets"].values():

            if str(record.get("guild_id")) != str(guild.id):
                continue

            if str(record.get("user_id")) != str(member.id):
                continue

            if record.get("ticket_type") != ticket_type:
                continue

            existing_tickets += 1

        if existing_tickets >= MAX_TICKETS_PER_TYPE:

            ticket_word = (
                "mass"
                if ticket_type == "mass"
                else "hire"
            )

            await interaction.response.send_message(
                f"{SPARK} you already have the maximum "
                f"of **{MAX_TICKETS_PER_TYPE} {ticket_word} tickets**.",
                ephemeral=True,
            )
            return

        username = member.name

        if ticket_type == "mass":
            channel_name = f"m {username}"
        else:
            channel_name = f"h {username}"

        channel_name = channel_name[:100]

        bot_member = guild.me

        if bot_member is None:
            await interaction.response.send_message(
                f"{SPARK} I couldn't find my server permissions.",
                ephemeral=True,
            )
            return

        if not bot_member.guild_permissions.manage_channels:
            await interaction.response.send_message(
                f"{SPARK} I need **Manage Channels** to create tickets.",
                ephemeral=True,
            )
            return

        await interaction.response.defer(
            ephemeral=True
        )

        try:

            overwrites = category.overwrites.copy()

            overwrites[guild.default_role] = (
                discord.PermissionOverwrite(
                    view_channel=False
                )
            )

            overwrites[member] = (
                discord.PermissionOverwrite(
                    view_channel=True,
                    send_messages=True,
                    read_message_history=True,
                    attach_files=True,
                    embed_links=True,
                )
            )

            overwrites[bot_member] = (
                discord.PermissionOverwrite(
                    view_channel=True,
                    send_messages=True,
                    read_message_history=True,
                    manage_channels=True,
                    manage_messages=True,
                )
            )

            ticket_channel = (
                await guild.create_text_channel(
                    name=channel_name,
                    category=category,
                    overwrites=overwrites,
                    reason=(
                        f"{ticket_type} ticket opened "
                        f"by {member}"
                    ),
                )
            )

            data = load_ticket_data()

            data["tickets"][str(ticket_channel.id)] = {
                "guild_id": guild.id,
                "channel_id": ticket_channel.id,
                "user_id": member.id,
                "ticket_type": ticket_type,
                "channel_name": ticket_channel.name,
                "opened_at": datetime.now(
                    timezone.utc
                ).isoformat(),
            }

            save_ticket_data(data)

            if ticket_type == "mass":
                opening_message = MASS_OPENING
            else:
                opening_message = HIRE_OPENING

            await ticket_channel.send(
                content=opening_message,
                view=CloseTicketView(self),
            )

            await interaction.followup.send(
                f"{SPARK} your ticket is ready: "
                f"{ticket_channel.mention}",
                ephemeral=True,
            )

            if interaction.message:

                try:

                    await interaction.message.edit(
                        view=TicketSelectView(self)
                    )

                except discord.HTTPException as error:

                    print(
                        f"Ticket menu reset error: "
                        f"{type(error).__name__}: {error}"
                    )

            print(
                f"Ticket created: "
                f"{ticket_channel.name} "
                f"({ticket_type}) "
                f"by {member}"
            )

        except discord.Forbidden:

            print(
                "Ticket creation failed: "
                "Discord denied a permission."
            )

            await interaction.followup.send(
                f"{SPARK} I don't have enough permissions "
                "to create the ticket.",
                ephemeral=True,
            )

        except discord.HTTPException as error:

            print(
                f"Ticket creation Discord error: "
                f"{type(error).__name__}: {error}"
            )

            await interaction.followup.send(
                f"{SPARK} Discord rejected the ticket.",
                ephemeral=True,
            )

        except Exception as error:

            print(
                f"Ticket creation error: "
                f"{type(error).__name__}: {error}"
            )

            await interaction.followup.send(
                f"{SPARK} something went wrong creating "
                "the ticket.",
                ephemeral=True,
            )


async def setup(bot):
    await bot.add_cog(
        Tickets(bot)
    )