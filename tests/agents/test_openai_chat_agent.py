import unittest
from unittest.mock import MagicMock, patch

from fluctlight.agents.openai_chat_agent import OpenAiChatAgent, create_reason_agent
from fluctlight.intent.message_intent import DEFAULT_CHAT_INTENT
from tests.data.imessages import MESSAGE_HELLO_WORLD, MESSAGE_HELLO_WORLD2
from tests.intergation_test_utils import skip_integration_tests


class TestOpenAiChatAgent(unittest.TestCase):
    @patch("fluctlight.agents.openai_chat_agent.chat_complete")
    def test_process_message_legacy_models(self, mock_chat_complete: MagicMock):
        # Mocking OpenAI response
        mock_response_text = "mocked response from OpenAI"
        mock_response = MagicMock()
        mock_response.choices = [
            MagicMock(message=MagicMock(content=mock_response_text))
        ]
        mock_chat_complete.return_value = mock_response
        agent = OpenAiChatAgent(chatbot_model_id="gpt-4o")

        response1 = agent.process_message(
            message=MESSAGE_HELLO_WORLD, message_intent=DEFAULT_CHAT_INTENT
        )
        response2 = agent.process_message(
            message=MESSAGE_HELLO_WORLD2, message_intent=DEFAULT_CHAT_INTENT
        )

        self.assertEqual(response1, [mock_response_text])
        self.assertEqual(response2, [mock_response_text])
        self.assertEqual(mock_chat_complete.call_count, 2)

        self.assertEqual(
            5, len(agent.message_buffer[MESSAGE_HELLO_WORLD.thread_message_id])
        )
        # Optionally, assert the types or contents of these messages, if needed:
        expected_order = ["system", "user", "assistant", "user", "assistant"]
        for i, message in enumerate(
            agent.message_buffer[MESSAGE_HELLO_WORLD.thread_message_id]
        ):
            # Replace 'type' with the actual key used to determine message type
            self.assertEqual(expected_order[i], message["role"])

    @patch("fluctlight.agents.openai_chat_agent.chat_complete")
    def test_process_message_plain_text_with_o1(self, mock_chat_complete: MagicMock):
        # O1-mini doesn't support system/developer role message.
        # Mocking OpenAI response
        mock_response_text = "mocked response from OpenAI"
        mock_response = MagicMock()
        mock_response.choices = [
            MagicMock(message=MagicMock(content=mock_response_text))
        ]
        mock_chat_complete.return_value = mock_response
        agent = OpenAiChatAgent(chatbot_model_id="o1-mini")

        response1 = agent.process_message(
            message=MESSAGE_HELLO_WORLD, message_intent=DEFAULT_CHAT_INTENT
        )
        response2 = agent.process_message(
            message=MESSAGE_HELLO_WORLD2, message_intent=DEFAULT_CHAT_INTENT
        )

        self.assertEqual(response1, [mock_response_text])
        self.assertEqual(response2, [mock_response_text])
        self.assertEqual(mock_chat_complete.call_count, 2)

        self.assertEqual(
            4, len(agent.message_buffer[MESSAGE_HELLO_WORLD.thread_message_id])
        )
        # Optionally, assert the types or contents of these messages, if needed:
        expected_order = ["user", "assistant", "user", "assistant"]
        for i, message in enumerate(
            agent.message_buffer[MESSAGE_HELLO_WORLD.thread_message_id]
        ):
            # Replace 'type' with the actual key used to determine message type
            self.assertEqual(expected_order[i], message["role"])

    @patch("fluctlight.agents.openai_chat_agent.chat_complete")
    def test_process_message_plain_text_same_thread(
        self, mock_chat_complete: MagicMock
    ):
        # Mocking OpenAI response
        mock_response_text = "mocked response from OpenAI"
        mock_response = MagicMock()
        mock_response.choices = [
            MagicMock(message=MagicMock(content=mock_response_text))
        ]
        mock_chat_complete.return_value = mock_response

        agent = OpenAiChatAgent()

        response = agent.process_message(
            MESSAGE_HELLO_WORLD, message_intent=DEFAULT_CHAT_INTENT
        )

        self.assertEqual(response, [mock_response_text])
        self.assertIn(MESSAGE_HELLO_WORLD.thread_message_id, agent.message_buffer)
        mock_chat_complete.assert_called_once()

    @unittest.skip("Deepseek api is not stable")
    @skip_integration_tests
    def test_reason_agent_process_messsage(self):
        agent = create_reason_agent()
        try:
            agent.process_message(
                message=MESSAGE_HELLO_WORLD, message_intent=DEFAULT_CHAT_INTENT
            )
        except Exception as e:
            self.fail(f"process_message raised an exception: {e}")


if __name__ == "__main__":
    unittest.main()
