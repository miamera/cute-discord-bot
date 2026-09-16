import asyncio
import random
import time

import discord
from discord import app_commands
from discord.ext import commands

from config import AUTORESPONDER_FILE
from utils.storage import load_json, save_json
from utils.variables import build_variables, replace_variables


# ╭──────────────────────────────────────────────╮
# │              ♡ cute auto responders ♡        │
# ╰──────────────────────────────────────────────╯

SPARK = "<a:00_spark:1547846651790626907>"

PINK = 0xFF9FCC
LIGHT_PINK = 0xFFD6E8
DARK_PINK = 0xE879AC
PURPLE_PINK = 0xD9B8FF

DEFAULT_DATA = {
    "responders": {}
}

COOLDOWNS = {}


# ╭──────────────────────────────────────────────╮
# │                    helpers                   │
# ╰──────────────────────────────────────────────╯

def load_responders():
    data = load_json(
        AUTORESPONDER_FILE,
        DEFAULT_DATA,
    )

    if "responders" not in data:
        data["responders"] = {}

    return data


def save_responders(data):
    save_json(
        AUTORESPONDER_FILE,
        data,
    )


def get_responder(data, responder_id):
    return data.get(
        "responders",
        {}
    ).get(
        str(responder_id)
    )


def is_staff(interaction: discord.Interaction):
    return (
        interaction.guild is not None
        and interaction.user.guild_permissions.manage_guild
    )


def replace(text, message):
    if not text:
        return ""

    variables = build_variables(
        user=message.author,
        guild=message.guild,
        channel=message.channel,
        member=message.author,
        message=message,
    )

    return replace_variables(
        text,
        variables,
    )


# ╭──────────────────────────────────────────────╮
# │                trigger matching              │
# ╰──────────────────────────────────────────────╯

def matches_trigger(
    content,
    trigger,
    match_type,
    case_sensitive,
):
    if not case_sensitive:
        content = content.lower()
        trigger = trigger.lower()

    if match_type == "exact":
        return content == trigger

    if match_type == "contains":
        return trigger in content

    if match_type == "starts":
        return content.startswith(trigger)

    if match_type == "ends":
        return content.endswith(trigger)

    return False


def responder_matches(responder, message):
    if not responder.get(
        "enabled",
        True,
    ):
        return False

    if not message.content:
        return False

    triggers = responder.get(
        "triggers",
        [],
    )

    if not triggers:
        return False

    match_type = responder.get(
        "match_type",
        "contains",
    )

    case_sensitive = responder.get(
        "case_sensitive",
        False,
    )

    return any(
        matches_trigger(
            message.content,
            trigger,
            match_type,
            case_sensitive,
        )
        for trigger in triggers
    )


# ╭──────────────────────────────────────────────╮
# │                  role checks                 │
# ╰──────────────────────────────────────────────╯

def passes_role_requirement(
    responder,
    member,
):
    required_roles = responder.get(
        "required_roles",
        [],
    )

    if not required_roles:
        return True

    member_roles = {
        role.id
        for role in getattr(
            member,
            "roles",
            [],
        )
    }

    matches = [
        int(role_id) in member_roles
        for role_id in required_roles
    ]

    requirement = responder.get(
        "role_requirement",
        "any",
    )

    if requirement == "all":
        return all(matches)

    return any(matches)


# ╭──────────────────────────────────────────────╮
# │                   cooldown                  │
# ╰──────────────────────────────────────────────╯

def cooldown_key(
    responder_id,
    message,
    scope,
):
    if scope == "user":
        return (
            responder_id,
            "user",
            message.author.id,
        )

    if scope == "channel":
        return (
            responder_id,
            "channel",
            message.channel.id,
        )

    return (
        responder_id,
        "server",
        message.guild.id,
    )


def on_cooldown(
    responder_id,
    message,
    responder,
):
    try:
        seconds = float(
            responder.get(
                "cooldown_seconds",
                0,
            )
        )
    except (
        TypeError,
        ValueError,
    ):
        seconds = 0

    if seconds <= 0:
        return False

    scope = responder.get(
        "cooldown_scope",
        "user",
    )

    key = cooldown_key(
        responder_id,
        message,
        scope,
    )

    now = time.monotonic()
    last = COOLDOWNS.get(
        key,
        0,
    )

    if now - last < seconds:
        return True

    COOLDOWNS[key] = now

    return False


# ╭──────────────────────────────────────────────╮
# │                    embed                   │
# ╰──────────────────────────────────────────────╯

def build_embed(
    responder,
    message,
):
    embed_data = responder.get(
        "embed",
        {},
    )

    if not embed_data.get(
        "enabled",
        False,
    ):
        return None

    title = replace(
        embed_data.get(
            "title",
            "",
        ),
        message,
    )

    description = replace(
        embed_data.get(
            "description",
            "",
        ),
        message,
    )

    embed = discord.Embed(
        title=title or None,
        description=description or None,
        color=PINK,
    )

    color = embed_data.get(
        "color",
        "",
    ).strip()

    if color:
        try:
            color = color.replace(
                "#",
                "",
            )

            embed.color = discord.Color(
                int(color, 16)
            )

        except ValueError:
            pass

    url = replace(
        embed_data.get(
            "url",
            "",
        ),
        message,
    )

    if url:
        embed.url = url

    thumbnail = replace(
        embed_data.get(
            "thumbnail",
            "",
        ),
        message,
    )

    if thumbnail:
        embed.set_thumbnail(
            url=thumbnail
        )

    image = replace(
        embed_data.get(
            "image",
            "",
        ),
        message,
    )

    if image:
        embed.set_image(
            url=image
        )

    footer = replace(
        embed_data.get(
            "footer",
            "",
        ),
        message,
    )

    footer_icon = replace(
        embed_data.get(
            "footer_icon",
            "",
        ),
        message,
    )

    if footer:
        if footer_icon:
            embed.set_footer(
                text=footer,
                icon_url=footer_icon,
            )
        else:
            embed.set_footer(
                text=footer,
            )

    author_name = replace(
        embed_data.get(
            "author_name",
            "",
        ),
        message,
    )

    author_icon = replace(
        embed_data.get(
            "author_icon",
            "",
        ),
        message,
    )

    if author_name:
        if author_icon:
            embed.set_author(
                name=author_name,
                icon_url=author_icon,
            )
        else:
            embed.set_author(
                name=author_name,
            )

    if embed_data.get(
        "timestamp",
        False,
    ):
        embed.timestamp = discord.utils.utcnow()

    return embed


# ╭──────────────────────────────────────────────╮
# │                create responder              │
# ╰──────────────────────────────────────────────╯

class CreateResponderModal(discord.ui.Modal):

    def __init__(self):
        super().__init__(
            title="♡ create responder"
        )

        self.name = discord.ui.TextInput(
            label="responder name",
            placeholder="welcome",
            required=True,
            max_length=50,
        )

        self.triggers = discord.ui.TextInput(
            label="triggers",
            placeholder="hello, hi, hey",
            style=discord.TextStyle.paragraph,
            required=True,
            max_length=1000,
        )

        self.responses = discord.ui.TextInput(
            label="responses",
            placeholder="hii {user} ♡",
            style=discord.TextStyle.paragraph,
            required=True,
            max_length=2000,
        )

        self.match_type = discord.ui.TextInput(
            label="match type",
            placeholder="exact / contains / starts / ends",
            default="contains",
            required=True,
            max_length=20,
        )

        self.add_item(self.name)
        self.add_item(self.triggers)
        self.add_item(self.responses)
        self.add_item(self.match_type)

    async def on_submit(
        self,
        interaction,
    ):
        if not is_staff(interaction):
            await interaction.response.send_message(
                "♡ you don't have permission to use this.",
                ephemeral=True,
            )
            return

        match_type = (
            self.match_type.value
            .strip()
            .lower()
        )

        if match_type not in {
            "exact",
            "contains",
            "starts",
            "ends",
        }:
            await interaction.response.send_message(
                "♡ use `exact`, `contains`, `starts`, or `ends`.",
                ephemeral=True,
            )
            return

        triggers = [
            item.strip()
            for item in self.triggers.value.split(",")
            if item.strip()
        ]

        responses = [
            item.strip()
            for item in self.responses.value.split("\n")
            if item.strip()
        ]

        data = load_responders()

        responder_id = str(
            int(
                time.time() * 1000000
            )
        )

        data["responders"][responder_id] = {
            "name": self.name.value.strip(),
            "enabled": True,
            "triggers": triggers,
            "responses": responses,
            "match_type": match_type,
            "case_sensitive": False,

            "response_mode": "send",

            "reactions": [],

            "nickname": "",
            "channel_name": "",
            "channel_category": "",

            "delete_trigger": False,
            "delete_response": False,
            "delete_response_delay": 0,

            "required_roles": [],
            "role_requirement": "any",

            "cooldown_seconds": 0,
            "cooldown_scope": "user",

            "embed": {
                "enabled": False,
                "title": "",
                "description": "",
                "color": "",
                "thumbnail": "",
                "image": "",
                "footer": "",
                "footer_icon": "",
                "author_name": "",
                "author_icon": "",
                "url": "",
                "timestamp": False,
            },
        }

        save_responders(data)

        await interaction.response.send_message(
            f"{SPARK} created **{self.name.value.strip()}** ♡",
            ephemeral=True,
        )


# ╭──────────────────────────────────────────────╮
# │                 trigger modal                │
# ╰──────────────────────────────────────────────╯

class TriggersModal(discord.ui.Modal):

    def __init__(
        self,
        responder_id,
    ):
        super().__init__(
            title="♡ trigger settings"
        )

        self.responder_id = responder_id

        data = load_responders()

        responder = get_responder(
            data,
            responder_id,
        )

        current_triggers = ", ".join(
            responder.get(
                "triggers",
                [],
            )
        )

        self.triggers = discord.ui.TextInput(
            label="triggers",
            default=current_triggers,
            placeholder="hello, hi, hey",
            style=discord.TextStyle.paragraph,
            required=True,
            max_length=1000,
        )

        self.match_type = discord.ui.TextInput(
            label="match type",
            default=responder.get(
                "match_type",
                "contains",
            ),
            placeholder="exact / contains / starts / ends",
            required=True,
            max_length=20,
        )

        self.case_sensitive = discord.ui.TextInput(
            label="case sensitive?",
            default=(
                "yes"
                if responder.get(
                    "case_sensitive",
                    False,
                )
                else "no"
            ),
            placeholder="yes / no",
            required=True,
            max_length=10,
        )

        self.add_item(self.triggers)
        self.add_item(self.match_type)
        self.add_item(self.case_sensitive)

    async def on_submit(
        self,
        interaction,
    ):
        data = load_responders()

        responder = get_responder(
            data,
            self.responder_id,
        )

        if not responder:
            await interaction.response.send_message(
                "♡ responder no longer exists.",
                ephemeral=True,
            )
            return

        match_type = (
            self.match_type.value
            .strip()
            .lower()
        )

        if match_type not in {
            "exact",
            "contains",
            "starts",
            "ends",
        }:
            await interaction.response.send_message(
                "♡ invalid match type.",
                ephemeral=True,
            )
            return

        responder["triggers"] = [
            item.strip()
            for item in self.triggers.value.split(",")
            if item.strip()
        ]

        responder["match_type"] = match_type

        responder["case_sensitive"] = (
            self.case_sensitive.value
            .strip()
            .lower()
            in {
                "yes",
                "true",
                "on",
            }
        )

        save_responders(data)

        await interaction.response.send_message(
            f"{SPARK} trigger settings saved ♡",
            ephemeral=True,
        )


# ╭──────────────────────────────────────────────╮
# │                 response modal               │
# ╰──────────────────────────────────────────────╯

class ResponsesModal(discord.ui.Modal):

    def __init__(
        self,
        responder_id,
    ):
        super().__init__(
            title="♡ response settings"
        )

        self.responder_id = responder_id

        data = load_responders()

        responder = get_responder(
            data,
            responder_id,
        )

        current = "\n".join(
            responder.get(
                "responses",
                [],
            )
        )

        self.responses = discord.ui.TextInput(
            label="responses",
            default=current,
            placeholder="one response per line",
            style=discord.TextStyle.paragraph,
            required=True,
            max_length=2000,
        )

        self.mode = discord.ui.TextInput(
            label="response mode",
            default=responder.get(
                "response_mode",
                "send",
            ),
            placeholder="send / reply / random",
            required=True,
            max_length=20,
        )

        self.add_item(self.responses)
        self.add_item(self.mode)

    async def on_submit(
        self,
        interaction,
    ):
        data = load_responders()

        responder = get_responder(
            data,
            self.responder_id,
        )

        if not responder:
            await interaction.response.send_message(
                "♡ responder no longer exists.",
                ephemeral=True,
            )
            return

        mode = (
            self.mode.value
            .strip()
            .lower()
        )

        if mode not in {
            "send",
            "reply",
            "random",
        }:
            await interaction.response.send_message(
                "♡ mode must be `send`, `reply`, or `random`.",
                ephemeral=True,
            )
            return

        responder["responses"] = [
            item.strip()
            for item in self.responses.value.split("\n")
            if item.strip()
        ]

        responder["response_mode"] = mode

        save_responders(data)

        await interaction.response.send_message(
            f"{SPARK} response settings saved ♡",
            ephemeral=True,
        )


# ╭──────────────────────────────────────────────╮
# │                 behavior modal               │
# ╰──────────────────────────────────────────────╯

class BehaviorModal(discord.ui.Modal):

    def __init__(
        self,
        responder_id,
    ):
        super().__init__(
            title="♡ message behavior"
        )

        self.responder_id = responder_id

        data = load_responders()

        responder = get_responder(
            data,
            responder_id,
        )

        self.delete_trigger = discord.ui.TextInput(
            label="delete trigger?",
            default=(
                "yes"
                if responder.get(
                    "delete_trigger",
                    False,
                )
                else "no"
            ),
            placeholder="yes / no",
            required=True,
            max_length=10,
        )

        self.delete_response = discord.ui.TextInput(
            label="delete response?",
            default=(
                "yes"
                if responder.get(
                    "delete_response",
                    False,
                )
                else "no"
            ),
            placeholder="yes / no",
            required=True,
            max_length=10,
        )

        self.delay = discord.ui.TextInput(
            label="response delete delay",
            default=str(
                responder.get(
                    "delete_response_delay",
                    0,
                )
            ),
            placeholder="seconds — 0 = immediately",
            required=True,
            max_length=20,
        )

        self.add_item(self.delete_trigger)
        self.add_item(self.delete_response)
        self.add_item(self.delay)

    async def on_submit(
        self,
        interaction,
    ):
        data = load_responders()

        responder = get_responder(
            data,
            self.responder_id,
        )

        if not responder:
            await interaction.response.send_message(
                "♡ responder no longer exists.",
                ephemeral=True,
            )
            return

        responder["delete_trigger"] = (
            self.delete_trigger.value
            .strip()
            .lower()
            in {
                "yes",
                "true",
                "on",
            }
        )

        responder["delete_response"] = (
            self.delete_response.value
            .strip()
            .lower()
            in {
                "yes",
                "true",
                "on",
            }
        )

        try:
            delay = max(
                0,
                float(
                    self.delay.value.strip()
                ),
            )
        except ValueError:
            delay = 0

        responder["delete_response_delay"] = delay

        save_responders(data)

        await interaction.response.send_message(
            f"{SPARK} message behavior saved ♡",
            ephemeral=True,
        )


# ╭──────────────────────────────────────────────╮
# │                reactions modal               │
# ╰──────────────────────────────────────────────╯

class ReactionsModal(discord.ui.Modal):

    def __init__(
        self,
        responder_id,
    ):
        super().__init__(
            title="♡ reaction settings"
        )

        self.responder_id = responder_id

        data = load_responders()

        responder = get_responder(
            data,
            responder_id,
        )

        current = " ".join(
            responder.get(
                "reactions",
                [],
            )
        )

        self.reactions = discord.ui.TextInput(
            label="reactions",
            default=current,
            placeholder="♡ <:customemoji:123456789>",
            required=False,
            max_length=500,
        )

        self.add_item(
            self.reactions
        )

    async def on_submit(
        self,
        interaction,
    ):
        data = load_responders()

        responder = get_responder(
            data,
            self.responder_id,
        )

        if not responder:
            await interaction.response.send_message(
                "♡ responder no longer exists.",
                ephemeral=True,
            )
            return

        responder["reactions"] = (
            self.reactions.value.split()
            if self.reactions.value.strip()
            else []
        )

        save_responders(data)

        await interaction.response.send_message(
            f"{SPARK} reactions saved ♡",
            ephemeral=True,
        )


# ╭──────────────────────────────────────────────╮
# │             member/channel modal             │
# ╰──────────────────────────────────────────────╯

class MemberChannelModal(discord.ui.Modal):

    def __init__(
        self,
        responder_id,
    ):
        super().__init__(
            title="♡ member + channel"
        )

        self.responder_id = responder_id

        data = load_responders()

        responder = get_responder(
            data,
            responder_id,
        )

        self.nickname = discord.ui.TextInput(
            label="member nickname",
            default=responder.get(
                "nickname",
                "",
            ),
            placeholder="leave blank for none",
            required=False,
            max_length=100,
        )

        self.channel_name = discord.ui.TextInput(
            label="channel name",
            default=responder.get(
                "channel_name",
                "",
            ),
            placeholder="leave blank for none",
            required=False,
            max_length=100,
        )

        self.channel_category = discord.ui.TextInput(
            label="category ID",
            default=responder.get(
                "channel_category",
                "",
            ),
            placeholder="category channel ID",
            required=False,
            max_length=30,
        )

        self.add_item(self.nickname)
        self.add_item(self.channel_name)
        self.add_item(self.channel_category)

    async def on_submit(
        self,
        interaction,
    ):
        data = load_responders()

        responder = get_responder(
            data,
            self.responder_id,
        )

        if not responder:
            await interaction.response.send_message(
                "♡ responder no longer exists.",
                ephemeral=True,
            )
            return

        responder["nickname"] = (
            self.nickname.value.strip()
        )

        responder["channel_name"] = (
            self.channel_name.value.strip()
        )

        responder["channel_category"] = (
            self.channel_category.value.strip()
        )

        save_responders(data)

        await interaction.response.send_message(
            f"{SPARK} member + channel settings saved ♡",
            ephemeral=True,
        )


# ╭──────────────────────────────────────────────╮
# │                  roles modal                 │
# ╰──────────────────────────────────────────────╯

class RolesModal(discord.ui.Modal):

    def __init__(
        self,
        responder_id,
    ):
        super().__init__(
            title="♡ required roles"
        )

        self.responder_id = responder_id

        data = load_responders()

        responder = get_responder(
            data,
            responder_id,
        )

        current = ", ".join(
            str(role_id)
            for role_id in responder.get(
                "required_roles",
                [],
            )
        )

        self.roles = discord.ui.TextInput(
            label="role IDs",
            default=current,
            placeholder="123456789, 987654321",
            required=False,
            max_length=500,
        )

        self.requirement = discord.ui.TextInput(
            label="requirement",
            default=responder.get(
                "role_requirement",
                "any",
            ),
            placeholder="any / all",
            required=True,
            max_length=10,
        )

        self.add_item(self.roles)
        self.add_item(self.requirement)

    async def on_submit(
        self,
        interaction,
    ):
        data = load_responders()

        responder = get_responder(
            data,
            self.responder_id,
        )

        if not responder:
            await interaction.response.send_message(
                "♡ responder no longer exists.",
                ephemeral=True,
            )
            return

        role_ids = []

        for value in self.roles.value.split(","):
            value = value.strip()

            if not value:
                continue

            try:
                role_ids.append(
                    int(value)
                )
            except ValueError:
                pass

        requirement = (
            self.requirement.value
            .strip()
            .lower()
        )

        if requirement not in {
            "any",
            "all",
        }:
            await interaction.response.send_message(
                "♡ requirement must be `any` or `all`.",
                ephemeral=True,
            )
            return

        responder["required_roles"] = role_ids
        responder["role_requirement"] = requirement

        save_responders(data)

        await interaction.response.send_message(
            f"{SPARK} role settings saved ♡",
            ephemeral=True,
        )


# ╭──────────────────────────────────────────────╮
# │                cooldown modal                │
# ╰──────────────────────────────────────────────╯

class CooldownModal(discord.ui.Modal):

    def __init__(
        self,
        responder_id,
    ):
        super().__init__(
            title="♡ cooldown"
        )

        self.responder_id = responder_id

        data = load_responders()

        responder = get_responder(
            data,
            responder_id,
        )

        self.seconds = discord.ui.TextInput(
            label="cooldown seconds",
            default=str(
                responder.get(
                    "cooldown_seconds",
                    0,
                )
            ),
            placeholder="0 = disabled",
            required=True,
            max_length=20,
        )

        self.scope = discord.ui.TextInput(
            label="cooldown scope",
            default=responder.get(
                "cooldown_scope",
                "user",
            ),
            placeholder="user / channel / server",
            required=True,
            max_length=20,
        )

        self.add_item(self.seconds)
        self.add_item(self.scope)

    async def on_submit(
        self,
        interaction,
    ):
        data = load_responders()

        responder = get_responder(
            data,
            self.responder_id,
        )

        if not responder:
            await interaction.response.send_message(
                "♡ responder no longer exists.",
                ephemeral=True,
            )
            return

        try:
            seconds = max(
                0,
                float(
                    self.seconds.value.strip()
                ),
            )
        except ValueError:
            await interaction.response.send_message(
                "♡ cooldown must be a number.",
                ephemeral=True,
            )
            return

        scope = (
            self.scope.value
            .strip()
            .lower()
        )

        if scope not in {
            "user",
            "channel",
            "server",
        }:
            await interaction.response.send_message(
                "♡ scope must be `user`, `channel`, or `server`.",
                ephemeral=True,
            )
            return

        responder["cooldown_seconds"] = seconds
        responder["cooldown_scope"] = scope

        save_responders(data)

        await interaction.response.send_message(
            f"{SPARK} cooldown saved ♡",
            ephemeral=True,
        )


# ╭──────────────────────────────────────────────╮
# │                  embed modal                 │
# ╰──────────────────────────────────────────────╯

class EmbedModal(discord.ui.Modal):

    def __init__(
        self,
        responder_id,
    ):
        super().__init__(
            title="♡ embed settings"
        )

        self.responder_id = responder_id

        data = load_responders()

        responder = get_responder(
            data,
            responder_id,
        )

        embed = responder.get(
            "embed",
            {},
        )

        self.enabled = discord.ui.TextInput(
            label="embed enabled?",
            default=(
                "yes"
                if embed.get(
                    "enabled",
                    False,
                )
                else "no"
            ),
            placeholder="yes / no",
            required=True,
            max_length=10,
        )

        self.title_input = discord.ui.TextInput(
            label="title",
            default=embed.get(
                "title",
                "",
            ),
            required=False,
            max_length=256,
        )

        self.description = discord.ui.TextInput(
            label="description",
            default=embed.get(
                "description",
                "",
            ),
            style=discord.TextStyle.paragraph,
            required=False,
            max_length=4000,
        )

        self.color = discord.ui.TextInput(
            label="color",
            default=embed.get(
                "color",
                "",
            ),
            placeholder="#FF9FCC",
            required=False,
            max_length=20,
        )

        self.url = discord.ui.TextInput(
            label="url",
            default=embed.get(
                "url",
                "",
            ),
            required=False,
            max_length=500,
        )

        self.add_item(self.enabled)
        self.add_item(self.title_input)
        self.add_item(self.description)
        self.add_item(self.color)
        self.add_item(self.url)

    async def on_submit(
        self,
        interaction,
    ):
        data = load_responders()

        responder = get_responder(
            data,
            self.responder_id,
        )

        if not responder:
            await interaction.response.send_message(
                "♡ responder no longer exists.",
                ephemeral=True,
            )
            return

        embed = responder.setdefault(
            "embed",
            {},
        )

        embed["enabled"] = (
            self.enabled.value
            .strip()
            .lower()
            in {
                "yes",
                "true",
                "on",
            }
        )

        embed["title"] = (
            self.title_input.value.strip()
        )

        embed["description"] = (
            self.description.value.strip()
        )

        embed["color"] = (
            self.color.value.strip()
        )

        embed["url"] = (
            self.url.value.strip()
        )

        save_responders(data)

        await interaction.response.send_message(
            f"{SPARK} embed settings saved ♡",
            ephemeral=True,
        )


# ╭──────────────────────────────────────────────╮
# │              embed extras modal              │
# ╰──────────────────────────────────────────────╯

class EmbedExtraModal(discord.ui.Modal):

    def __init__(
        self,
        responder_id,
    ):
        super().__init__(
            title="♡ embed extras"
        )

        self.responder_id = responder_id

        data = load_responders()

        responder = get_responder(
            data,
            responder_id,
        )

        embed = responder.get(
            "embed",
            {},
        )

        self.thumbnail = discord.ui.TextInput(
            label="thumbnail URL",
            default=embed.get(
                "thumbnail",
                "",
            ),
            required=False,
            max_length=500,
        )

        self.image = discord.ui.TextInput(
            label="image URL",
            default=embed.get(
                "image",
                "",
            ),
            required=False,
            max_length=500,
        )

        self.footer = discord.ui.TextInput(
            label="footer",
            default=embed.get(
                "footer",
                "",
            ),
            required=False,
            max_length=2048,
        )

        self.footer_icon = discord.ui.TextInput(
            label="footer icon URL",
            default=embed.get(
                "footer_icon",
                "",
            ),
            required=False,
            max_length=500,
        )

        self.timestamp = discord.ui.TextInput(
            label="timestamp?",
            default=(
                "yes"
                if embed.get(
                    "timestamp",
                    False,
                )
                else "no"
            ),
            placeholder="yes / no",
            required=True,
            max_length=10,
        )

        self.add_item(self.thumbnail)
        self.add_item(self.image)
        self.add_item(self.footer)
        self.add_item(self.footer_icon)
        self.add_item(self.timestamp)

    async def on_submit(
        self,
        interaction,
    ):
        data = load_responders()

        responder = get_responder(
            data,
            self.responder_id,
        )

        if not responder:
            await interaction.response.send_message(
                "♡ responder no longer exists.",
                ephemeral=True,
            )
            return

        embed = responder.setdefault(
            "embed",
            {},
        )

        embed["thumbnail"] = (
            self.thumbnail.value.strip()
        )

        embed["image"] = (
            self.image.value.strip()
        )

        embed["footer"] = (
            self.footer.value.strip()
        )

        embed["footer_icon"] = (
            self.footer_icon.value.strip()
        )

        embed["timestamp"] = (
            self.timestamp.value
            .strip()
            .lower()
            in {
                "yes",
                "true",
                "on",
            }
        )

        save_responders(data)

        await interaction.response.send_message(
            f"{SPARK} embed extras saved ♡",
            ephemeral=True,
        )


# ╭──────────────────────────────────────────────╮
# │               embed author modal             │
# ╰──────────────────────────────────────────────╯

class EmbedAuthorModal(discord.ui.Modal):

    def __init__(
        self,
        responder_id,
    ):
        super().__init__(
            title="♡ embed author"
        )

        self.responder_id = responder_id

        data = load_responders()

        responder = get_responder(
            data,
            responder_id,
        )

        embed = responder.get(
            "embed",
            {},
        )

        self.author_name = discord.ui.TextInput(
            label="author name",
            default=embed.get(
                "author_name",
                "",
            ),
            required=False,
            max_length=256,
        )

        self.author_icon = discord.ui.TextInput(
            label="author icon URL",
            default=embed.get(
                "author_icon",
                "",
            ),
            required=False,
            max_length=500,
        )

        self.add_item(
            self.author_name
        )

        self.add_item(
            self.author_icon
        )

    async def on_submit(
        self,
        interaction,
    ):
        data = load_responders()

        responder = get_responder(
            data,
            self.responder_id,
        )

        if not responder:
            await interaction.response.send_message(
                "♡ responder no longer exists.",
                ephemeral=True,
            )
            return

        embed = responder.setdefault(
            "embed",
            {},
        )

        embed["author_name"] = (
            self.author_name.value.strip()
        )

        embed["author_icon"] = (
            self.author_icon.value.strip()
        )

        save_responders(data)

        await interaction.response.send_message(
            f"{SPARK} embed author saved ♡",
            ephemeral=True,
        )


# ╭──────────────────────────────────────────────╮
# │                editor buttons                │
# ╰──────────────────────────────────────────────╯

class ResponderEditorView(discord.ui.View):

    def __init__(
        self,
        responder_id,
    ):
        super().__init__(
            timeout=300
        )

        self.responder_id = responder_id

    async def interaction_check(
        self,
        interaction,
    ):
        if not is_staff(interaction):
            await interaction.response.send_message(
                "♡ staff only.",
                ephemeral=True,
            )
            return False

        return True

    @discord.ui.button(
        label="♡ triggers",
        style=discord.ButtonStyle.secondary,
    )
    async def triggers(
        self,
        interaction,
        button,
    ):
        await interaction.response.send_modal(
            TriggersModal(
                self.responder_id
            )
        )

    @discord.ui.button(
        label="♡ responses",
        style=discord.ButtonStyle.secondary,
    )
    async def responses(
        self,
        interaction,
        button,
    ):
        await interaction.response.send_modal(
            ResponsesModal(
                self.responder_id
            )
        )

    @discord.ui.button(
        label="୨୧ behavior",
        style=discord.ButtonStyle.secondary,
    )
    async def behavior(
        self,
        interaction,
        button,
    ):
        await interaction.response.send_modal(
            BehaviorModal(
                self.responder_id
            )
        )

    @discord.ui.button(
        label="♡ reactions",
        style=discord.ButtonStyle.secondary,
    )
    async def reactions(
        self,
        interaction,
        button,
    ):
        await interaction.response.send_modal(
            ReactionsModal(
                self.responder_id
            )
        )

    @discord.ui.button(
        label="୨୧ member/channel",
        style=discord.ButtonStyle.secondary,
    )
    async def member_channel(
        self,
        interaction,
        button,
    ):
        await interaction.response.send_modal(
            MemberChannelModal(
                self.responder_id
            )
        )

    @discord.ui.button(
        label="♡ roles",
        style=discord.ButtonStyle.secondary,
    )
    async def roles(
        self,
        interaction,
        button,
    ):
        await interaction.response.send_modal(
            RolesModal(
                self.responder_id
            )
        )

    @discord.ui.button(
        label="♡ cooldown",
        style=discord.ButtonStyle.secondary,
    )
    async def cooldown(
        self,
        interaction,
        button,
    ):
        await interaction.response.send_modal(
            CooldownModal(
                self.responder_id
            )
        )

    @discord.ui.button(
        label="♡ embed",
        style=discord.ButtonStyle.secondary,
    )
    async def embed(
        self,
        interaction,
        button,
    ):
        await interaction.response.send_modal(
            EmbedModal(
                self.responder_id
            )
        )

    @discord.ui.button(
        label="୨୧ embed extras",
        style=discord.ButtonStyle.secondary,
    )
    async def embed_extras(
        self,
        interaction,
        button,
    ):
        await interaction.response.send_modal(
            EmbedExtraModal(
                self.responder_id
            )
        )

    @discord.ui.button(
        label="♡ embed author",
        style=discord.ButtonStyle.secondary,
    )
    async def embed_author(
        self,
        interaction,
        button,
    ):
        await interaction.response.send_modal(
            EmbedAuthorModal(
                self.responder_id
            )
        )

    @discord.ui.button(
        label="♡ toggle",
        style=discord.ButtonStyle.success,
        row=4,
    )
    async def toggle(
        self,
        interaction,
        button,
    ):
        data = load_responders()

        responder = get_responder(
            data,
            self.responder_id,
        )

        if not responder:
            await interaction.response.send_message(
                "♡ responder no longer exists.",
                ephemeral=True,
            )
            return

        responder["enabled"] = not responder.get(
            "enabled",
            True,
        )

        save_responders(data)

        status = (
            "enabled ♡"
            if responder["enabled"]
            else "disabled ♡"
        )

        await interaction.response.send_message(
            f"{SPARK} responder {status}",
            ephemeral=True,
        )

    @discord.ui.button(
        label="♡ delete",
        style=discord.ButtonStyle.danger,
        row=4,
    )
    async def delete(
        self,
        interaction,
        button,
    ):
        data = load_responders()

        responders = data.get(
            "responders",
            {},
        )

        if self.responder_id not in responders:
            await interaction.response.send_message(
                "♡ responder no longer exists.",
                ephemeral=True,
            )
            return

        del responders[
            self.responder_id
        ]

        save_responders(data)

        await interaction.response.send_message(
            f"{SPARK} responder deleted ♡",
            ephemeral=True,
        )


# ╭──────────────────────────────────────────────╮
# │                 selector                     │
# ╰──────────────────────────────────────────────╯

class ResponderSelect(discord.ui.Select):

    def __init__(self):
        data = load_responders()

        responders = data.get(
            "responders",
            {},
        )

        options = []

        for responder_id, responder in list(
            responders.items()
        )[:25]:

            status = (
                "♡ enabled"
                if responder.get(
                    "enabled",
                    True,
                )
                else "୨୧ disabled"
            )

            options.append(
                discord.SelectOption(
                    label=responder.get(
                        "name",
                        responder_id,
                    )[:100],
                    value=responder_id,
                    description=status,
                )
            )

        if not options:
            options.append(
                discord.SelectOption(
                    label="♡ no responders yet",
                    value="none",
                )
            )

        super().__init__(
            placeholder="୨୧ choose a responder...",
            options=options,
        )

    async def callback(
        self,
        interaction,
    ):
        if not is_staff(interaction):
            await interaction.response.send_message(
                "♡ staff only.",
                ephemeral=True,
            )
            return

        selected = self.values[0]

        if selected == "none":
            await interaction.response.send_message(
                "♡ create a responder first.",
                ephemeral=True,
            )
            return

        data = load_responders()

        responder = get_responder(
            data,
            selected,
        )

        if not responder:
            await interaction.response.send_message(
                "♡ responder no longer exists.",
                ephemeral=True,
            )
            return

        enabled = (
            "♡ enabled"
            if responder.get(
                "enabled",
                True,
            )
            else "୨୧ disabled"
        )

        embed = discord.Embed(
            title=(
                f"୨୧ ♡ {responder.get('name', 'responder')} ♡ ୨୧"
            ),
            description=(
                "₊˚⊹♡₊˚⊹♡₊˚⊹♡₊˚⊹\n\n"
                f"status: **{enabled}**\n"
                f"triggers: **{len(responder.get('triggers', []))}**\n"
                f"responses: **{len(responder.get('responses', []))}**\n\n"
                "꒰ა  choose what you'd like to edit  ໒꒱"
            ),
            color=PINK,
        )

        await interaction.response.send_message(
            embed=embed,
            view=ResponderEditorView(
                selected
            ),
            ephemeral=True,
        )


# ╭──────────────────────────────────────────────╮
# │                  main panel                  │
# ╰──────────────────────────────────────────────╯

class AutoResponderPanel(
    discord.ui.View
):

    def __init__(self):
        super().__init__(
            timeout=300
        )

        self.add_item(
            ResponderSelect()
        )

    async def interaction_check(
        self,
        interaction,
    ):
        if not is_staff(interaction):
            await interaction.response.send_message(
                "♡ staff only.",
                ephemeral=True,
            )
            return False

        return True

    @discord.ui.button(
        label="♡ create",
        style=discord.ButtonStyle.success,
    )
    async def create(
        self,
        interaction,
        button,
    ):
        await interaction.response.send_modal(
            CreateResponderModal()
        )

    @discord.ui.button(
        label="୨୧ refresh",
        style=discord.ButtonStyle.secondary,
    )
    async def refresh(
        self,
        interaction,
        button,
    ):
        await interaction.response.edit_message(
            embed=discord.Embed(
                title="୨୧ ♡ auto responders ♡ ୨୧",
                description=(
                    "₊˚⊹♡₊˚⊹♡₊˚⊹♡₊˚⊹\n\n"
                    "manage all your cute little automatic responses ♡\n\n"
                    "꒰ა select one below or create a new one ໒꒱\n\n"
                    "୨୧ ─────────────── ୨୧"
                ),
                color=PINK,
            ),
            view=AutoResponderPanel(),
        )


# ╭──────────────────────────────────────────────╮
# │                responder cog                 │
# ╰──────────────────────────────────────────────╯

class AutoResponders(commands.Cog):

    def __init__(
        self,
        bot,
    ):
        self.bot = bot

    @app_commands.command(
        name="ars",
        description="Manage automatic responders."
    )
    @app_commands.default_permissions(
        manage_guild=True
    )
    async def ars(
        self,
        interaction,
    ):
        if not is_staff(interaction):
            await interaction.response.send_message(
                "♡ staff only.",
                ephemeral=True,
            )
            return

        embed = discord.Embed(
            title="୨୧ ♡ auto responders ♡ ୨୧",
            description=(
                "₊˚⊹♡₊˚⊹♡₊˚⊹♡₊˚⊹\n\n"
                "manage all your cute little automatic responses ♡\n\n"
                "꒰ა select one below or create a new one ໒꒱\n\n"
                "୨୧ ─────────────── ୨୧"
            ),
            color=PINK,
        )

        await interaction.response.send_message(
            embed=embed,
            view=AutoResponderPanel(),
            ephemeral=True,
        )

    @commands.Cog.listener()
    async def on_message(
        self,
        message,
    ):
        # Ignore bots/webhooks
        if message.author.bot:
            return

        # Responders only work in servers
        if message.guild is None:
            return

        # Ignore messages with no readable content
        if not message.content:
            return

        data = load_responders()

        responders = data.get(
            "responders",
            {},
        )

        for responder_id, responder in responders.items():

            try:
                # ── enabled ──────────────────────────────
                if not responder.get(
                    "enabled",
                    True,
                ):
                    continue

                # ── trigger ─────────────────────────────
                if not responder_matches(
                    responder,
                    message,
                ):
                    continue

                # ── required roles ───────────────────────
                if not passes_role_requirement(
                    responder,
                    message.author,
                ):
                    continue

                # ── cooldown ────────────────────────────
                if on_cooldown(
                    responder_id,
                    message,
                    responder,
                ):
                    continue

                responses = responder.get(
                    "responses",
                    [],
                )

                if not responses:
                    continue

                # ── response selection ──────────────────
                mode = responder.get(
                    "response_mode",
                    "send",
                )

                if mode == "random":
                    response_text = random.choice(
                        responses
                    )
                    send_mode = "send"

                else:
                    response_text = responses[0]
                    send_mode = mode

                response_text = replace(
                    response_text,
                    message,
                )

                # ── embed ───────────────────────────────
                embed = build_embed(
                    responder,
                    message,
                )

                # ── send response ───────────────────────
                sent_message = None

                try:
                    if send_mode == "reply":
                        sent_message = await message.reply(
                            response_text or None,
                            embed=embed,
                            mention_author=False,
                        )
                    else:
                        sent_message = await message.channel.send(
                            response_text or None,
                            embed=embed,
                        )

                except (
                    discord.Forbidden,
                    discord.HTTPException,
                ) as error:
                    print(
                        f"Auto responder send error "
                        f"({responder_id}): "
                        f"{type(error).__name__}: {error}"
                    )
                    continue

                # ── reactions ───────────────────────────
                for reaction in responder.get(
                    "reactions",
                    [],
                ):
                    try:
                        await message.add_reaction(
                            reaction
                        )

                    except (
                        discord.Forbidden,
                        discord.HTTPException,
                    ):
                        pass

                # ── member nickname ─────────────────────
                nickname = replace(
                    responder.get(
                        "nickname",
                        "",
                    ),
                    message,
                )

                if nickname:
                    try:
                        await message.author.edit(
                            nick=nickname
                        )

                    except (
                        discord.Forbidden,
                        discord.HTTPException,
                    ):
                        pass

                # ── channel rename ──────────────────────
                channel_name = replace(
                    responder.get(
                        "channel_name",
                        "",
                    ),
                    message,
                )

                if channel_name:
                    try:
                        await message.channel.edit(
                            name=channel_name
                        )

                    except (
                        discord.Forbidden,
                        discord.HTTPException,
                    ):
                        pass

                # ── channel category ────────────────────
                category_id = responder.get(
                    "channel_category",
                    "",
                )

                if category_id:
                    try:
                        category = (
                            message.guild.get_channel(
                                int(category_id)
                            )
                        )

                        if isinstance(
                            category,
                            discord.CategoryChannel,
                        ):
                            await message.channel.edit(
                                category=category
                            )

                    except (
                        ValueError,
                        TypeError,
                        discord.Forbidden,
                        discord.HTTPException,
                    ):
                        pass

                # ── delete trigger ──────────────────────
                if responder.get(
                    "delete_trigger",
                    False,
                ):
                    try:
                        await message.delete()

                    except (
                        discord.NotFound,
                        discord.Forbidden,
                        discord.HTTPException,
                    ):
                        pass

                # ── delete response ─────────────────────
                if (
                    sent_message
                    and responder.get(
                        "delete_response",
                        False,
                    )
                ):
                    try:
                        delay = max(
                            0,
                            float(
                                responder.get(
                                    "delete_response_delay",
                                    0,
                                )
                            ),
                        )
                    except (
                        TypeError,
                        ValueError,
                    ):
                        delay = 0

                    if delay > 0:
                        await asyncio.sleep(
                            delay
                        )

                    try:
                        await sent_message.delete()

                    except (
                        discord.NotFound,
                        discord.Forbidden,
                        discord.HTTPException,
                    ):
                        pass

            except Exception as error:
                # One broken responder should never stop
                # every other responder from working.
                print(
                    f"Auto responder error "
                    f"({responder_id}): "
                    f"{type(error).__name__}: {error}"
                )


async def setup(bot):
    await bot.add_cog(
        AutoResponders(bot)
    )