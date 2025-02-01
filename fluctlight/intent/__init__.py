from .intent_agent import IntentAgent
from .rag_intent_matcher import RagIntentMatcher
from .intent_matcher_base import IntentMatcher, IntentMatcherBase
from fluctlight.settings import INTENT_LLM_MATCHING


def get_default_intent_matcher(agents: list[IntentAgent]) -> IntentMatcher:
    if INTENT_LLM_MATCHING:
        return RagIntentMatcher(agents=agents)
    else:
        return IntentMatcherBase(agents=agents)


__all__ = ["get_default_intent_matcher"]
