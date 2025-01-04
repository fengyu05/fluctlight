from .intent_agent import IntentAgent
from .rag_intent_matcher import RagIntentMatcher
from .openai_intent_matcher import OpenAIIntentMatcher
from .intent_matcher_base import IntentMatcher, IntentMatcherBase
from fluctlight.settings import INTENT_LLM_MATCHING, FIREWORKS_API_KEY


def get_default_intent_matcher(agents: list[IntentAgent]) -> IntentMatcher:
    if INTENT_LLM_MATCHING:
        if FIREWORKS_API_KEY:
            return RagIntentMatcher(agents=agents)
        else:
            return OpenAIIntentMatcher(agents=agents)
    else:
        return IntentMatcherBase(agents=agents)


__all__ = ["get_default_intent_matcher"]
