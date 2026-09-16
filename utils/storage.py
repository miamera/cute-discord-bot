import json
from pathlib import Path


def load_json(path: Path, default=None):
    if default is None:
        default = {}

    if not path.exists():
        save_json(path, default)
        return default

    try:
        with path.open("r", encoding="utf-8") as file:
            return json.load(file)
    except (json.JSONDecodeError, OSError):
        return default


def save_json(path: Path, data):
    path.parent.mkdir(parents=True, exist_ok=True)

    with path.open("w", encoding="utf-8") as file:
        json.dump(data, file, indent=4, ensure_ascii=False)


def get_guild(data, guild_id: int):
    guild_id = str(guild_id)

    if guild_id not in data:
        data[guild_id] = {}

    return data[guild_id]


def delete_guild(data, guild_id: int):
    data.pop(str(guild_id), None)