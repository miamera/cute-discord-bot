from datetime import datetime


def build_variables(
    *,
    user=None,
    guild=None,
    channel=None,
    member=None,
    message=None,
):
    now = datetime.now()

    variables = {}

    # ─────────────────────────────────────────
    # USER
    # ─────────────────────────────────────────

    if user:
        variables.update({
            "user": user.mention,
            "user_mention": user.mention,
            "user_name": user.name,
            "user_display_name": getattr(user, "display_name", user.name),
            "user_id": str(user.id),
            "user_avatar": user.display_avatar.url,
        })

    # ─────────────────────────────────────────
    # MEMBER
    # ─────────────────────────────────────────

    if member:
        variables.update({
            "member": member.mention,
            "member_name": member.name,
            "member_display_name": member.display_name,
            "member_id": str(member.id),
            "member_avatar": member.display_avatar.url,
            "member_created_at": member.created_at.strftime("%Y-%m-%d"),
            "member_joined_at": (
                member.joined_at.strftime("%Y-%m-%d")
                if member.joined_at
                else ""
            ),
        })

    # ─────────────────────────────────────────
    # SERVER
    # ─────────────────────────────────────────

    if guild:
        variables.update({
            "server": guild.name,
            "server_name": guild.name,
            "server_id": str(guild.id),
            "server_avatar": (
                guild.icon.url
                if guild.icon
                else ""
            ),
            "server_owner": (
                guild.owner.mention
                if guild.owner
                else ""
            ),
            "server_member_count": str(guild.member_count),
        })

    # ─────────────────────────────────────────
    # CHANNEL
    # ─────────────────────────────────────────

    if channel:
        variables.update({
            "channel": channel.mention,
            "channel_name": channel.name,
            "channel_id": str(channel.id),
            "channel_category": (
                channel.category.name
                if getattr(channel, "category", None)
                else ""
            ),
        })

    # ─────────────────────────────────────────
    # MESSAGE
    # ─────────────────────────────────────────

    if message:
        variables.update({
            "message_id": str(message.id),
            "message_content": message.content,
            "message_url": message.jump_url,
        })

    # ─────────────────────────────────────────
    # TIME
    # ─────────────────────────────────────────

    variables.update({
        "time": now.strftime("%H:%M"),
        "time_12": now.strftime("%I:%M %p"),
        "date": now.strftime("%Y-%m-%d"),
        "datetime": now.strftime("%Y-%m-%d %H:%M:%S"),
        "year": now.strftime("%Y"),
        "month": now.strftime("%m"),
        "day": now.strftime("%d"),
    })

    return variables


def replace_variables(text: str, variables: dict):
    if not text:
        return text

    for name, value in variables.items():
        text = text.replace("{" + name + "}", str(value))

    return text