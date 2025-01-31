import unittest
from unittest.mock import patch, MagicMock
from openai.types.chat import ChatCompletion
from openai.types.chat.chat_completion import Choice
from openai.types.chat.chat_completion_message import ChatCompletionMessage
from fluctlight.open.chat import (
    get_provider_and_model_id,
    get_message_from_completion,
    get_parsed_choice_from_completion,
    chat_complete,
    structure_chat_completion,
    simple_assistant,
    structure_simple_assistant,
)


class TestChat(unittest.TestCase):
    def test_get_provider_and_model_id(self):
        self.assertEqual(get_provider_and_model_id("openai:gpt-3"), ("openai", "gpt-3"))
        self.assertEqual(
            get_provider_and_model_id("DEEPSEEK:model"), ("deepseek", "model")
        )
        self.assertEqual(get_provider_and_model_id("gpt-3"), ("openai", "gpt-3"))

    def test_get_message_from_completion(self):
        mock_completion = MagicMock(spec=ChatCompletion)
        mock_completion.choices = [
            MagicMock(
                spec=Choice,
                message=MagicMock(spec=ChatCompletionMessage, content="test content"),
            )
        ]
        self.assertEqual(get_message_from_completion(mock_completion), "test content")

    def test_get_parsed_choice_from_completion(self):
        mock_completion = MagicMock(spec=ChatCompletion)
        mock_completion.choices = [
            MagicMock(
                spec=Choice,
                message=MagicMock(spec=ChatCompletionMessage, parsed={"key": "value"}),
            )
        ]
        self.assertEqual(
            get_parsed_choice_from_completion(mock_completion), {"key": "value"}
        )

    @patch("fluctlight.open.chat.get_open_client")
    def test_chat_complete(self, mock_get_client):
        mock_client = MagicMock()
        mock_response = MagicMock(spec=ChatCompletion)
        mock_client.chat.completions.create.return_value = mock_response
        mock_get_client.return_value = mock_client

        messages = [{"role": "user", "content": "test"}]
        response = chat_complete(messages=messages, model_key="openai:gpt-3")

        self.assertEqual(response, mock_response)
        mock_client.chat.completions.create.assert_called_with(
            model="gpt-3",
            messages=messages,
        )

    @patch("fluctlight.open.chat.get_open_client")
    def test_structure_chat_completion(self, mock_get_client):
        mock_client = MagicMock()
        mock_response = MagicMock(spec=ChatCompletion)
        mock_client.beta.chat.completions.parse.return_value = mock_response
        mock_get_client.return_value = mock_client

        messages = [{"role": "user", "content": "test"}]
        response = structure_chat_completion(
            output_schema=dict, messages=messages, model_key="openai:gpt-3"
        )

        self.assertEqual(response, mock_response)
        mock_client.beta.chat.completions.parse.assert_called_with(
            model="gpt-3",
            messages=messages,
            response_format=dict,
        )

    @patch("fluctlight.open.chat.chat_complete")
    def test_simple_assistant(self, mock_chat_complete):
        mock_completion = MagicMock(spec=ChatCompletion)
        mock_completion.choices = [
            MagicMock(
                spec=Choice,
                message=MagicMock(spec=ChatCompletionMessage, content="test response"),
            )
        ]
        mock_chat_complete.return_value = mock_completion

        response = simple_assistant("test prompt")
        self.assertEqual(response, "test response")
        mock_chat_complete.assert_called_once()

    @patch("fluctlight.open.chat.structure_chat_completion")
    def test_structure_simple_assistant(self, mock_structure_chat_complete):
        mock_completion = MagicMock(spec=ChatCompletion)
        mock_completion.choices = [
            MagicMock(
                spec=Choice,
                message=MagicMock(spec=ChatCompletionMessage, parsed={"key": "value"}),
            )
        ]
        mock_structure_chat_complete.return_value = mock_completion

        response = structure_simple_assistant("test prompt", dict)
        self.assertEqual(response, {"key": "value"})
        mock_structure_chat_complete.assert_called_once()


if __name__ == "__main__":
    unittest.main()
