from pathlib import Path

# ─────────────────────────────────────────────
# PATHS
# ─────────────────────────────────────────────

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"

DATA_DIR.mkdir(exist_ok=True)


# ─────────────────────────────────────────────
# BOT STYLE
# ─────────────────────────────────────────────

BOT_NAME = "your bot"

DIVIDER = "── ୨୧ ・⸝⸝"

SUCCESS = "♡"
ERROR = "♡"
INFO = "✧"
ARROW = "୨୧"


# ─────────────────────────────────────────────
# DEFAULT COLORS
# ─────────────────────────────────────────────

DEFAULT_COLOR = 0x2B2028
SUCCESS_COLOR = 0xB9A3AD
ERROR_COLOR = 0x6E4C5A
INFO_COLOR = 0x8C7580


# ─────────────────────────────────────────────
# FILES
# ─────────────────────────────────────────────

CONFIG_FILE = DATA_DIR / "config.json"
AUTORESPONDER_FILE = DATA_DIR / "autoresponders.json"
TICKET_FILE = DATA_DIR / "tickets.json"
REACTION_ROLE_FILE = DATA_DIR / "reaction_roles.json"