from abc import ABC, abstractmethod

from fluctlight.agent_catalog.catalog_manager import get_catalog_manager
from fluctlight.data_model.interface import IMessage
from fluctlight.intent.intent_agent import IntentAgent
from fluctlight.intent.message_intent import (
    DEFAULT_CHAT_INTENT,
    UNKNOWN_INTENT,
    MessageIntent,
    get_leading_emoji,
    get_message_intent_by_text,
)
from fluctlight.logger import get_logger
from fluctlight.settings import (
    INTENT_LLM_MATCHING,
    INTENT_CHAR_MATCHING,
    INTENT_EMOJI_MATCHING,
    CHAR_AGENT_BIND,
)

logger = get_logger(__name__)


class IntentMatcher(ABC):
    intent_by_thread: dict[str, MessageIntent]
    agents: list[IntentAgent]
    _chars_map: dict[str, str] | None = None

    def __init__(
        self,
        agents: list[IntentAgent],
        disable_cache: bool = False,
    ) -> None:
        self.intent_by_thread = {}
        self.agents = agents
        self.disable_cache = disable_cache
        self.catalog_manager = get_catalog_manager()

    @abstractmethod
    def parse_intent_key(self, text: str) -> str:
        pass

    def match_message_intent(self, message: IMessage) -> MessageIntent:
        """
        Determines the intent of a message using thread ID or text analysis.

        Args:
            message (IMessage): The message object to analyze.

        Returns:
            MessageIntent: The detected message intent.
        """
        if not self.disable_cache:
            if message.thread_message_id in self.intent_by_thread:
                return self.intent_by_thread[message.thread_message_id]

        message_intent = UNKNOWN_INTENT
        if not message.text:
            message_intent = DEFAULT_CHAT_INTENT
        else:
            # emoji > character > llm match
            if INTENT_EMOJI_MATCHING and message_intent.unknown:
                message_intent = get_message_intent_by_text(message.text)
            if INTENT_CHAR_MATCHING and message_intent.unknown:
                message_intent = self.get_char_agent_intent(
                    intent=message_intent, text=message.text
                )
            if INTENT_LLM_MATCHING and message_intent.unknown:
                message_intent = self.get_llm_agent_intent(
                    intent=message_intent, text=message.text
                )
        if message_intent.unknown:
            message_intent.key = "CHAT"
            message_intent.metadata["fallback_to_chat"] = True

        logger.info("Matched intent", intent=message_intent)
        if not self.disable_cache:
            self.intent_by_thread[message.thread_message_id] = message_intent
        return message_intent

    def get_char_emoji_map(self) -> dict[str, str]:
        if self._chars_map is None:
            chars_map = {}
            for char_id, character in self.catalog_manager.characters.items():
                chars_map[char_id] = char_id
                chars_map[character.name] = char_id
            self._chars_map = chars_map
        return self._chars_map

    def get_char_agent_intent(self, intent: MessageIntent, text: str) -> MessageIntent:
        if CHAR_AGENT_BIND:
            intent.key = "CHAR"
            intent.metadata = {"char_id": CHAR_AGENT_BIND}
            intent.unknown = False
            intent.metadata["char_bind"] = True
        else:
            emoji = get_leading_emoji(text)
            chars_map = self.get_char_emoji_map()
            if emoji in chars_map:
                intent.key = "CHAR"
                intent.metadata = {"char_id": chars_map[emoji]}
                intent.unknown = False
                intent.metadata["char_match"] = True
        return intent

    def get_llm_agent_intent(self, intent: MessageIntent, text: str) -> MessageIntent:
        intent.key = self.parse_intent_key(text)
        intent.unknown = False
        intent.metadata["llm_match"] = True
        return intent


class IntentMatcherBase(IntentMatcher):
    def __init__(
        self,
        agents: list[IntentAgent],
        disable_cache: bool = False,
    ) -> None:
        super().__init__(agents=agents, disable_cache=disable_cache)

    def parse_intent_key(self, text: str) -> MessageIntent:
        return "CHAT"
