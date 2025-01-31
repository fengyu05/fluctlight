from pydantic import BaseModel, field_validator
from typing_extensions import TypeAlias

from fluctlight.utt.emoji import get_leading_emoji

_METHOD = "method"
_DEFAULT = "default"

MessageIntentMetadataType: TypeAlias = str | bool | float | int | None


class MessageIntent(BaseModel):
    key: str
    unknown: bool = False
    reason: bool = False
    search: bool = False
    metadata: dict[str, MessageIntentMetadataType] = {}

    @field_validator("key")
    @classmethod
    def uppercase_key(cls, v):
        if not isinstance(v, str):
            raise ValueError("The key must be a string.")
        return v.upper()

    def equal_wo_metadata(self, other: "MessageIntent") -> bool:
        return (
            self.key == other.key
            and self.reason == other.reason
            and self.search == other.search
            and self.unknown == other.unknown
        )

    def set_metadata(self, **kwargs: MessageIntentMetadataType):
        """Set multiple metadata key-value pairs at once.

        Args:
            kwargs: Key-value pairs where the key is a string, and the value is of type MessageIntentMetaData.
        """
        for key, value in kwargs.items():
            self.metadata[key] = value

    def get_metadata(self, key: str) -> MessageIntentMetadataType:
        return self.metadata.get(key, None)


def create_intent(
    key: str = "", reason: bool = False, search: bool = False, unknown: bool = False
) -> MessageIntent:
    return MessageIntent(key=key, reason=reason, search=search, unknown=unknown)


UNKNOWN_INTENT = create_intent(unknown=True, key="CHAT")
DEFAULT_CHAT_INTENT = MessageIntent(key="CHAT", metadata={_METHOD: _DEFAULT})

_EMOJI_INTENT_MAP = {
    "MIAO": ["cat"],
    "SHOPPING_ASSIST": ["shop"],
}

_INTENT_BY_EMOJI = {
    emoji: intent for intent, emojis in _EMOJI_INTENT_MAP.items() for emoji in emojis
}

_EMJOI_VARIANTS = {
    "REASON": ["reason", "reasoning", "think", "thinking_face"],
    "SEARCH": ["search", "web", "mag"],
}


def has_emoji_variants(key: str, text: str) -> bool:
    """Check if text contains any emoji variant for the given key.

    Args:
        key: Key in _EMJOI_VARIANTS to check ("REASON", "SEARCH", etc)
        text: Text to check for emoji variants

    Returns:
        bool: True if any variant found as :variant: in text
    """
    if key not in _EMJOI_VARIANTS:
        return False

    return any(f":{variant}:" in text for variant in _EMJOI_VARIANTS[key])


def get_message_intent_by_text(text: str) -> MessageIntent:
    emoji = get_leading_emoji(text)
    key = ""
    if emoji in _INTENT_BY_EMOJI:
        key = _INTENT_BY_EMOJI[emoji]
        unknown = False
    else:
        unknown = True

    reason = has_emoji_variants("REASON", text)
    search = has_emoji_variants("SEARCH", text)
    return create_intent(
        key=key,
        unknown=unknown,
        reason=reason,
        search=search,
    )
