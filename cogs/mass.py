import discord
from discord import app_commands
from discord.ext import commands
import asyncio

from config import TICKET_FILE
from utils.storage import load_json


BUTTERFLY = "<:4butterfly:1547846639312699473>"
SPARK = "<:z_0001:1551608220664201247>"

MASS_TICKET_CATEGORY_ID = 1549007825198387312

START_MESSAGE = "https://discord.gg/HZSmHkGscc"


def get_ticket_data():
    return load_json(
        TICKET_FILE,
        {
            "tickets": {},
            "mass_completed": {},
            "hire_completed": {},
        },
    )


def get_current_ticket(channel_id: int):
    data = get_ticket_data()

    ticket = data.get(
        "tickets",
        {},
    ).get(
        str(channel_id)
    )

    return ticket


def get_mass_level(user_id: int):
    data = get_ticket_data()

    completed = data.get(
        "mass_completed",
        {},
    )

    try:
        return int(
            completed.get(
                str(user_id),
                0,
            )
        )
    except (
        TypeError,
        ValueError,
    ):
        return 0


def is_mass_ticket(
    interaction: discord.Interaction,
):
    if interaction.guild is None:
        return False

    channel = interaction.channel

    # First use the saved ticket record when available.
    ticket = get_current_ticket(
        channel.id
    )

    if ticket:
        ticket_type = str(
            ticket.get(
                "ticket_type",
                ""
            )
        ).lower().strip()

        if ticket_type == "mass":
            return True

    # Reliable fallback for Mass tickets.
    # Mass tickets are created as `m username`
    # inside the Mass ticket category.
    if (
        channel.category_id
        == MASS_TICKET_CATEGORY_ID
        and channel.name.lower().startswith("m-")
    ):
        return True

    return False


def is_ticket_user(
    interaction: discord.Interaction,
):
    ticket = get_current_ticket(
        interaction.channel.id
    )

    if not ticket:
        return True

    return int(
        ticket.get(
            "user_id",
            interaction.user.id,
        )
    ) == interaction.user.id


class MassInfoModal(discord.ui.Modal):
    def __init__(
        self,
        sep_time: str,
        owner_id: int,
    ):
        super().__init__(
            title=f"{SPARK}     ﹕  details"
        )

        self.sep_time = sep_time
        self.owner_id = owner_id

        self.ad = discord.ui.TextInput(
            label="ad",
            placeholder="♡ paste ad here...",
            style=discord.TextStyle.paragraph,
            required=True,
            max_length=2000,
        )

        self.reqs = discord.ui.TextInput(
            label="reqs",
            placeholder="♡ paste reqs here...",
            style=discord.TextStyle.paragraph,
            required=True,
            max_length=2000,
        )

        self.add_item(self.ad)
        self.add_item(self.reqs)

    async def on_submit(
        self,
        interaction: discord.Interaction,
    ):
        if not is_mass_ticket(interaction):
            await interaction.response.send_message(
                f"{BUTTERFLY} this can only be used in a mass ticket.",
                ephemeral=True,
            )
            return

        if (
            interaction.user.id
            != self.owner_id
            and not interaction.user.guild_permissions.manage_channels
        ):
            await interaction.response.send_message(
                f"{BUTTERFLY} only the ticket user or staff can use this.",
                ephemeral=True,
            )
            return

        await interaction.response.defer(
            ephemeral=True
        )

        channel = interaction.channel

        messages = []

        try:
            ad_message = await channel.send(
                self.ad.value.strip()
            )

            messages.append(
                ad_message
            )

            reqs_message = await channel.send(
                self.reqs.value.strip()
            )

            messages.append(
                reqs_message
            )

            time_message = await channel.send(
                f"` {self.sep_time} `"
            )

            messages.append(
                time_message
            )

        except discord.Forbidden:
            await interaction.followup.send(
                f"{BUTTERFLY} I don't have permission to send messages here.",
                ephemeral=True,
            )
            return

        except discord.HTTPException as error:
            print(
                f"Mass message error: "
                f"{type(error).__name__}: {error}"
            )

            await interaction.followup.send(
                f"{BUTTERFLY} Discord rejected one of the messages.",
                ephemeral=True,
            )
            return

        # Pin every message.
        for message in messages:
            try:
                await message.pin(
                    reason="Mass process"
                )
            except (
                discord.Forbidden,
                discord.HTTPException,
            ):
                pass

        await interaction.followup.send(
            f"{SPARK} mass details sent + pinned\n\n-# click start when u are ready to start posting",
            ephemeral=True,
        )

        await channel.send(
            view=MassStartView()
        )


class SepTimeSelect(
    discord.ui.Select
):
    def __init__(
        self,
        owner_id: int,
        level: int,
    ):
        self.owner_id = owner_id
        self.level = level

        options = [
            discord.SelectOption(
                label="batch",
                value="batch",
                description=None,
                emoji=f"{BUTTERFLY}",
            ),
            discord.SelectOption(
                label="2h",
                value="2h",
                description=None,
                emoji=f"{SPARK}",
            ),
            discord.SelectOption(
                label="5h",
                value="5h",
                description=None,
                emoji=f"{BUTTERFLY}",
            ),
        ]

        if level >= 5:
            options.extend(
                [
                    discord.SelectOption(
                        label="10h",
                        value="10h",
                        description=None,
                        emoji=f"{SPARK}",
                    ),
                    discord.SelectOption(
                        label="20h",
                        value="20h",
                        description=None,
                        emoji=f"{BUTTERFLY}",
                    ),
                    discord.SelectOption(
                        label="30h",
                        value="30h",
                        description=None,
                        emoji=f"{SPARK}",
                    ),
                ]
            )

        super().__init__(
            placeholder="♡ choose sep time...",
            options=options,
            min_values=1,
            max_values=1,
        )

    async def callback(
        self,
        interaction: discord.Interaction,
    ):
        if interaction.user.id != self.owner_id:
            await interaction.response.send_message(
                f"{BUTTERFLY} this menu isn't for you.",
                ephemeral=True,
            )
            return

        selected = self.values[0]

        await interaction.response.send_modal(
            MassInfoModal(
                sep_time=selected,
                owner_id=self.owner_id,
            )
        )

        async def reset_menu():
            await asyncio.sleep(0.3)

            try:
                await interaction.message.edit(
                    view=MassSetupView(
                        owner_id=self.owner_id,
                        level=self.level,
                    )
                )
            except (
                discord.NotFound,
                discord.Forbidden,
                discord.HTTPException,
            ):
                pass

        asyncio.create_task(
            reset_menu()
        )


class MassSetupView(
    discord.ui.View
):
    def __init__(
        self,
        owner_id: int,
        level: int,
    ):
        super().__init__(
            timeout=180
        )

        self.owner_id = owner_id

        self.add_item(
            SepTimeSelect(
                owner_id,
                level,
            )
        )

    async def interaction_check(
        self,
        interaction: discord.Interaction,
    ):
        if interaction.user.id != self.owner_id:
            await interaction.response.send_message(
                f"{BUTTERFLY} this menu isn't for you.",
                ephemeral=True,
            )
            return False

        return True


class MassStartView(
    discord.ui.View
):
    def __init__(self):
        super().__init__(
            timeout=None
        )

    @discord.ui.button(
        label="♡ start",
        style=discord.ButtonStyle.success,
        custom_id="mass:start",
    )
    async def start(
        self,
        interaction: discord.Interaction,
        button: discord.ui.Button,
    ):
        if not is_mass_ticket(interaction):
            await interaction.response.send_message(
                f"{BUTTERFLY} this button can only be used in a mass ticket.",
                ephemeral=True,
            )
            return

        if (
            not is_ticket_user(interaction)
            and not interaction.user.guild_permissions.manage_channels
        ):
            await interaction.response.send_message(
                f"{BUTTERFLY} only the ticket user or staff can start this.",
                ephemeral=True,
            )
            return

        channel = interaction.channel

        ticket = get_current_ticket(
            channel.id
        )

        username = None

        if ticket:
            opener_id = ticket.get(
                "user_id"
            )

            if opener_id:
                member = interaction.guild.get_member(
                    int(opener_id)
                )

                if member:
                    username = member.name

        if not username:
            username = interaction.user.name

        new_name = f"w2p {username}"

        try:
            await channel.edit(
                name=new_name
            )
        except discord.Forbidden:
            await interaction.response.send_message(
                f"{BUTTERFLY} I don't have permission to rename this channel.",
                ephemeral=True,
            )
            return

        except discord.HTTPException:
            await interaction.response.send_message(
                f"{BUTTERFLY} Discord rejected the channel rename.",
                ephemeral=True,
            )
            return

        await interaction.response.defer()

        try:
            await channel.send(
                START_MESSAGE
            )
        except (
            discord.Forbidden,
            discord.HTTPException,
        ):
            pass

        button.disabled = True

        try:
            await interaction.message.edit(
                view=self
            )
        except (
            discord.NotFound,
            discord.Forbidden,
            discord.HTTPException,
        ):
            pass


class Mass(commands.Cog):
    def __init__(
        self,
        bot: commands.Bot,
    ):
        self.bot = bot

    async def cog_load(self):
        self.bot.add_view(
            MassStartView()
        )

    @app_commands.command(
        name="mass",
        description="♡ Start the Mass process :D"
    )
    async def mass(
        self,
        interaction: discord.Interaction,
    ):
        # Acknowledge immediately so Discord does not time out
        # while the setup view is being prepared.
        await interaction.response.defer(
            ephemeral=True
        )

        try:
            if not is_mass_ticket(interaction):
                await interaction.followup.send(
                    f"{BUTTERFLY} `/mass` can only be used inside a Mass ticket.",
                    ephemeral=True,
                )
                return

            if (
                not is_ticket_user(interaction)
                and not interaction.user.guild_permissions.manage_channels
            ):
                await interaction.followup.send(
                    f"{BUTTERFLY} only the ticket user or staff can use this.",
                    ephemeral=True,
                )
                return

            ticket = get_current_ticket(
                interaction.channel.id
            )

            # If staff runs /mass, use the ticket opener's level,
            # not the staff member's level.
            level_user_id = interaction.user.id

            if ticket and ticket.get("user_id"):
                try:
                    level_user_id = int(
                        ticket.get("user_id")
                    )
                except (
                    TypeError,
                    ValueError,
                ):
                    pass

            level = get_mass_level(
                level_user_id
            )

            extra = (
                "\n\n ` earned seps ! `\n"
                "-# 10h\n"
                "-# 20h\n"
                "-# 30h"
                if level >= 5
                else ""
            )

            embed = discord.Embed(
                title="♡ Get started !!",
                description=("choose ur sep time\n"
                             "-# have ur ad ready before choosing :3\n\n\n"
                    "` ♡ avb: `\n"
                    "-# batch\n"
                    "-# 2h\n"
                    "-# 5h"
                    f"{extra}\n\n"
                    f"ur mass lvl is: ` {level}/5 `"
                ),
                color=0x393A41,
            )

            await interaction.followup.send(
                embed=embed,
                view=MassSetupView(
                    owner_id=interaction.user.id,
                    level=level,
                ),
                ephemeral=True,
            )

        except Exception as error:
            print(
                f"/mass error: "
                f"{type(error).__name__}: {error}"
            )

            try:
                await interaction.followup.send(
                    f"{BUTTERFLY} something went wrong while opening the Mass setup. "
                    f"Check the Railway logs for `/mass error`.",
                    ephemeral=True,
                )
            except (
                discord.HTTPException,
                discord.NotFound,
            ):
                pass



async def setup(
    bot: commands.Bot,
):
    await bot.add_cog(
        Mass(bot)
    )