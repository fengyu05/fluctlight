import os
from typing import Any, Optional

import fluctlight.constants as C


def config_default(key: str, default_value: Optional[Any] = None) -> Any:
    return os.environ.get(key, default_value)


def config_default_float(key: str, default_value: Any = 0.0) -> float:
    return float(os.environ.get(key, default_value))


def config_default_int(key: str, default_value: Any = 0) -> float:
    return int(os.environ.get(key, default_value))


_TRUTHY_VALUES = {"true", "1", "yes", "t", "y"}


def config_default_bool(key: str, default_value: bool = False) -> bool:
    return str(os.environ.get(key, default_value)).lower() in _TRUTHY_VALUES


# App config
ENV = config_default("ENV", "dev")
APP_NAME = config_default("APP_NAME", "botchan")
LOG_LEVEL = config_default("LOG_LEVEL", "INFO")
DEBUG_MODE = config_default_bool("DEBUG_MODE", False)  # For debug print
TEST_MODE = config_default_bool("TEST_MODE", False)  # For unit test
APP_PORT = config_default_int("APP_PORT", 3000)

BOT_CLIENT = config_default("BOT_CLIENT", "SLACK").upper()

# Bot config
BOT_NAME = config_default("BOT_NAME", APP_NAME)

# Slack credential
SLACK_APP_OAUTH_TOKENS_FOR_WS = config_default("SLACK_APP_OAUTH_TOKENS_FOR_WS")
SLACK_APP_LEVEL_TOKEN = config_default("SLACK_APP_LEVEL_TOKEN")

# Discord credential
DISCORD_BOT_TOKEN = config_default("DISCORD_BOT_TOKEN")

DISCORD_BOT_GUILD_ID = config_default_int("DISCORD_BOT_GUILD_ID")

DISCORD_BOT_DEVELOPER_ROLE = config_default("DISCORD_BOT_DEVELOPER_ROLE", "developer")

# OPENAI API KEY
OPENAI_API_KEY = config_default("OPENAI_API_KEY")

# OPENAI GPT MODEL ID
OPENAI_GPT_MODEL_ID = config_default("OPENAI_GPT_MODEL_ID", C.GPT_4O)
OPENAI_CHATBOT_MODEL_ID = config_default("OPENAI_CHATBOT_MODEL_ID", C.GPT_O1_MINI)

# Whether to use char agent to match intent
CHAR_AGENT_MATCHING = config_default_bool("CHAR_AGENT_MATCHING", True)

# Whether to use LLM to match message intent
LLM_INTENT_MATCHING = config_default_bool("LLM_INTENT_MATCHING", False)

# Whether to use SQL char DB
USE_SQL_CHAR_DB = config_default_bool("USE_SQL_CHAR_DB", False)

# Default tmp path
TMP_PATH = config_default("TMP", "/tmp/")

# TTS section
TTS_ENGINE = config_default("TTS_ENGINE", "ELEVEN_LABS")
# TTS API
# XTTS
# XTTS_API_KEY = config_default("XTTS_API_KEY", "")
# XTTS_API_URL = config_default("XTTS_API_URL")

# LEVEN_LABS TTS
ELEVEN_LABS_API_KEY = config_default("ELEVEN_LABS_API_KEY")

# Speech to text section
SPEECH_TO_TEXT_ENGINE = config_default("SPEECH_TO_TEXT_ENGINE", "OPENAI_WHISPER")


# Slack transcrition callback waiting time
SLACK_TRANSCRIBE_WAIT_SEC = config_default_float("SLACK_TRANSCRIBE_WAIT_SEC", 10)

# Web server config
SQLALCHEMY_DATABASE_URL = config_default("SQLALCHEMY_DATABASE_URL")

# Override Chroma DB
OVERWRITE_CHROMA = config_default_bool("OVERWRITE_CHROMA", False)
CHAR_CATALOG_DIR = config_default("CHAR_CATALOG_DIR", "/app_data/chars_catalog")
CHROMA_DB_DIR = config_default("CHROMA_DB_DIR", "/app_data/chroma.db")
CHROMA_DB_COLLECTION_NAME = config_default("CHROMA_DB_COLLECTION_NAME", "characters")


# Setting methods
def is_slack_bot() -> bool:
    return BOT_CLIENT == "SLACK"


def is_discord_bot() -> bool:
    return BOT_CLIENT == "DISCORD"
