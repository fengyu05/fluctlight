import os
import unittest

from langchain_core.messages import HumanMessage

from fluctlight.agents.expert.shopping_assist import (
    INTENT_KEY as shopping_assisist_intent_key,
)
from fluctlight.agents.expert.shopping_assist import (
    create_shopping_assist_task_graph_agent,
)
from fluctlight.agents.miao_agent import MiaoAgent
from fluctlight.agents.openai_chat_agent import OpenAiChatAgent
from fluctlight.intent.intent_candidate import IntentCandidate
from fluctlight.intent.rag_intent_matcher import GraphState, RagIntentMatcher
from tests.intergation_test_utils import skip_integration_tests


class TestRagIntentMatcher(unittest.TestCase):
    def setUp(self) -> None:
        agents = [
            OpenAiChatAgent(),  ## Handle simple chat
            MiaoAgent(),
            create_shopping_assist_task_graph_agent(),
        ]
        self.intent_matcher = RagIntentMatcher(agents)
        return super().setUp()

    @skip_integration_tests
    def test_parse_intent_chat(self):
        result = self.intent_matcher.parse_intent_key("Let's have a free chat")
        self.assertEqual(result.key, "CHAT")

    @skip_integration_tests
    def test_parse_intent_shopping(self):
        result = self.intent_matcher.parse_intent_key("Help me order sth")
        self.assertEqual(result.key, shopping_assisist_intent_key)

    @skip_integration_tests
    def test_match_intent_node(self):
        state = GraphState(
            messages=[HumanMessage("Help me order sth")],
            intent_candidate=None,
            intent_json_payload=None,
        )
        result_state = self.intent_matcher.match_intent_node(state)
        self.assertIsNotNone(result_state["intent_candidate"])
        assert result_state["intent_candidate"]
        self.assertEqual(
            result_state["intent_candidate"].intent_primary,
            shopping_assisist_intent_key,
        )

    def test_parse_final_state_with_primary_intent(self):
        state = GraphState(
            messages=[],
            intent_candidate=IntentCandidate(
                understanding="",
                intent_primary=shopping_assisist_intent_key,
                intent_secondary="other",
            ),
            intent_json_payload=None,
        )
        message_intent_key = self.intent_matcher.parse_final_state(state)
        self.assertEqual(message_intent_key, shopping_assisist_intent_key)

    def test_parse_final_state_with_secondary_intent(self):
        state = GraphState(
            messages=[],
            intent_candidate=IntentCandidate(
                understanding="",
                intent_primary="other",
                intent_secondary=shopping_assisist_intent_key,
            ),
            intent_json_payload=None,
        )
        message_intent_key = self.intent_matcher.parse_final_state(state)
        self.assertEqual(message_intent_key, shopping_assisist_intent_key)


# Run the tests
if __name__ == "__main__":
    # Set the environment variable
    os.environ["RUN_INTEGRATION_TESTS"] = "1"

    unittest.main()
