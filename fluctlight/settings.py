from fluctlight.utt.config import (
    config_default,
    config_default_bool,
    config_default_int,
    config_default_float,
)
import fluctlight.constants as C

# App config
ENV = config_default("ENV", "dev")
APP_NAME = config_default("APP_NAME", "Fluctlight")
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


def validate_discord_bot_access_mode(value: str) -> bool:
    if value in ["all", "member"]:
        return True
    return value.startswith("role:")


DISCORD_BOT_ACCESS_MODE = config_default(
    "DISCORD_BOT_ACCESS_MODE", "all", validator=validate_discord_bot_access_mode
)


# OPENAI API KEY
OPENAI_API_KEY = config_default("OPENAI_API_KEY")

# OPENAI GPT MODEL ID
OPENAI_GPT_MODEL_ID = config_default("OPENAI_GPT_MODEL_ID", C.GPT_4O)
OPENAI_CHATBOT_MODEL_ID = config_default("OPENAI_CHATBOT_MODEL_ID", C.GPT_O1_MINI)

# FIREWORKS API KEY, alt to OpenAI
FIREWORKS_API_KEY = config_default("FIREWORKS_API_KEY")

# Intent matching config
INTENT_CHAR_MATCHING = config_default_bool("INTENT_CHAR_MATCHING", False)
INTENT_LLM_MATCHING = config_default_bool("INTENT_LLM_MATCHING", False)
INTENT_EMOJI_MATCHING = config_default_bool("INTENT_EMOJI_MATCHING", False)

# For INTENT_CHAR_MATCHING
CHAR_AGENT_BIND = config_default("CHAR_AGENT_BIND")

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
