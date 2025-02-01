import unittest
from unittest.mock import MagicMock, patch

from fluctlight.agents.openai_chat_agent import OpenAiChatAgent
from fluctlight.intent.message_intent import create_intent, DEFAULT_CHAT_INTENT
from tests.data.imessages import (
    MESSAGE_HELLO_WORLD,
    MESSAGE_HELLO_WORLD2,
    MESSAGE_WITH_IMAGE,
)


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
        agent = OpenAiChatAgent(chat_model_id="gpt-4o")

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
    def test_process_message_plain_text_reasoning(self, mock_chat_complete: MagicMock):
        # O series model doesn't support system/developer role message.
        # Mocking OpenAI response
        mock_response_text = "= 7"
        mock_response = MagicMock()
        mock_response.choices = [
            MagicMock(message=MagicMock(content=mock_response_text))
        ]
        mock_chat_complete.return_value = mock_response
        agent = OpenAiChatAgent(reason_model_id="o3-mini", chat_model_id="gpt-4o")

        test_message_reason = MESSAGE_HELLO_WORLD.model_copy()
        test_message_reason.text = "what is 1+2*3 :think: "

        response1 = agent.process_message(
            message=test_message_reason,
            message_intent=create_intent(key="CHAT", reason=True),
        )

        self.assertEqual(response1, [mock_response_text])
        mock_chat_complete.assert_called_once_with(
            model_key="o3-mini",
            messages=[
                {
                    "role": "user",
                    "content": [{"type": "text", "text": test_message_reason.text}],
                },
            ],
        )

        self.assertEqual(
            2, len(agent.message_buffer[test_message_reason.thread_message_id])
        )
        # Optionally, assert the types or contents of these messages, if needed:
        expected_order = ["user", "assistant"]
        for i, message in enumerate(
            agent.message_buffer[test_message_reason.thread_message_id]
        ):
            # Replace 'type' with the actual key used to determine message type
            self.assertEqual(expected_order[i], message["role"])

    @patch("fluctlight.agents.openai_chat_agent.base64_encode_media")
    @patch("fluctlight.agents.openai_chat_agent.chat_complete")
    def test_process_message_with_vision_input(
        self, mock_chat_complete: MagicMock, mock_base64_encode_media: MagicMock
    ):
        # Mocking OpenAI response
        mock_response_text = "a image of a cat"
        mock_response = MagicMock()
        mock_response.choices = [
            MagicMock(message=MagicMock(content=mock_response_text))
        ]
        mock_chat_complete.return_value = mock_response
        base64_image_encoded = "base64_image_encoded"
        mock_base64_encode_media.return_value = base64_image_encoded

        agent = OpenAiChatAgent(
            chat_model_id="gpt-chat",
            vision_model_id="gpt-vision",
            reason_model_id="gpt-reason",
        )
        test_message_image = MESSAGE_WITH_IMAGE.model_copy()
        test_message_image.text = ":think: what in this image?"

        response = agent.process_message(
            test_message_image, message_intent=DEFAULT_CHAT_INTENT
        )

        self.assertEqual(response, [mock_response_text])
        mock_chat_complete.assert_called_once_with(
            model_key="gpt-vision",
            messages=[
                {
                    "role": "system",
                    "content": "\nYou are Fluctlight a helpful assistant bot.\n",
                },
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": test_message_image.text},
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:image/jpeg;base64,{base64_image_encoded}",
                                "detail": "low",
                            },
                        },
                    ],
                },
            ],
        )
        mock_base64_encode_media.assert_called_once()


if __name__ == "__main__":
    unittest.main()
