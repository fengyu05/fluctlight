from fluctlight.settings import GPT_CHAT_MODEL

from .base import CharacterAgent
from .openai_character_agent import OpenAICharacterAgent


def create_default_character_agent() -> CharacterAgent:
    return OpenAICharacterAgent(model=GPT_CHAT_MODEL)
