import unittest

from fluctlight.agents.miao_agent import MiaoAgent
from fluctlight.agents.openai_chat_agent import OpenAiChatAgent
from fluctlight.intent.intent_agent import IntentAgent
from fluctlight.intent.intent_matcher_base import IntentMatcher, IntentMatcherBase
from fluctlight.intent.message_intent import (
    DEFAULT_CHAT_INTENT,
    MessageIntent,
    create_intent,
)
from tests.data.imessages import (
    MESSAGE_HELLO_WORLD,
    MESSAGE_HELLO_WORLD2,
)

_TEST_INTENT = create_intent("test")


class IntentMacherForTest(IntentMatcher):
    def __init__(self, agents: list[IntentAgent]) -> None:
        super().__init__(agents=agents)

    def parse_intent(self, text: str) -> MessageIntent:
        return _TEST_INTENT


class TestMessageIntentAgent(unittest.TestCase):
    def setUp(self):
        from fluctlight.agents.expert.shopping_assist import (
            create_shopping_assist_task_graph_agent,
        )

        self.intent_matcher = IntentMatcherBase(
            agents=[
                OpenAiChatAgent(),
                MiaoAgent(),
                create_shopping_assist_task_graph_agent(),
            ],
        )

    def test_intent_by_thread(self):
        test_intent_matcher = IntentMacherForTest(
            agents=[
                OpenAiChatAgent(),
            ],
        )
        message1 = MESSAGE_HELLO_WORLD
        message2 = MESSAGE_HELLO_WORLD2

        # Assert the intent cache starts empty
        self.assertNotIn(
            message1.thread_message_id, test_intent_matcher.intent_by_thread
        )
        # Process the first message
        test_intent_matcher.match_message_intent(message1)

        intent_1 = test_intent_matcher.intent_by_thread[message1.thread_message_id]
        self.assertEqual(intent_1, _TEST_INTENT)

        # Process the second message in the same thread
        test_intent_matcher.match_message_intent(message2)

        intent_2 = test_intent_matcher.intent_by_thread[message2.thread_message_id]
        # Assert the two intents should be equal since they are from the same thread
        self.assertEqual(intent_1, intent_2)

    def test_intent_match_by_emoji_cat(self):
        message = MESSAGE_HELLO_WORLD

        message.text = ":cat:"
        result = self.intent_matcher.match_message_intent(message)
        expected_miao = MessageIntent(key="MIAO")
        self.assertEqual(result.key, expected_miao.key)

    def test_intent_match_by_emoji_shop(self):
        message = MESSAGE_HELLO_WORLD
        message.text = ":shop:"
        result = self.intent_matcher.match_message_intent(message)
        expected_shopping_assist = MessageIntent(key="SHOPPING_ASSIST")
        self.assertEqual(result.key, expected_shopping_assist.key)

    def test_no_text_returns_chat_intent(self):
        message = MESSAGE_HELLO_WORLD
        message.text = ""
        result = self.intent_matcher.match_message_intent(message)

        self.assertEqual(result, DEFAULT_CHAT_INTENT)


if __name__ == "__main__":
    unittest.main()
