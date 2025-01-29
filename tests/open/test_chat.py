import unittest
from unittest.mock import patch, MagicMock
from fluctlight.open.chat import (
    chat_complete,
    structure_chat_completion,
    simple_assistant,
    structure_simple_assistant,
)
from openai.types.chat.chat_completion import ChatCompletion
from openai.types.chat import ParsedChatCompletion


class TestChatFunctions(unittest.TestCase):
    @patch("fluctlight.open.chat.OPENAI_CLIENT")
    @patch("fluctlight.open.chat.get_alt_client_from_model_key")
    def test_chat_complete(self, mock_get_alt_client, mock_openai_client):
        mock_openai_client.chat.completions.create.return_value = MagicMock(
            spec=ChatCompletion
        )
        mock_alt_client = MagicMock()
        mock_get_alt_client.return_value = mock_alt_client

        # Test with OpenAI provider
        response = chat_complete(
            messages=[{"role": "user", "content": "Hello"}],
            model_key="openai:gpt-3",
            temperature=0.5,
        )
        self.assertIsInstance(response, ChatCompletion)
        mock_openai_client.chat.completions.create.assert_called_once_with(
            temperature=0.5,
            model="gpt-3",
            messages=[{"role": "user", "content": "Hello"}],
        )

        # Test with alternative provider
        mock_alt_client.chat.completions.create.return_value = MagicMock(
            spec=ChatCompletion
        )
        response = chat_complete(
            messages=[{"role": "user", "content": "Hello"}],
            model_key="deepseek:model",
            temperature=0.5,
        )
        self.assertIsInstance(response, ChatCompletion)
        mock_get_alt_client.assert_called_once_with("deepseek:model")
        mock_alt_client.chat.completions.create.assert_called_once_with(
            temperature=0.5,
            model="model",
            messages=[{"role": "user", "content": "Hello"}],
        )

    @patch("fluctlight.open.chat.OPENAI_CLIENT")
    @patch("fluctlight.open.chat.get_alt_client_from_model_key")
    def test_structure_chat_completion(self, mock_get_alt_client, mock_openai_client):
        mock_openai_client.beta.chat.completions.parse.return_value = MagicMock(
            spec=ParsedChatCompletion
        )
        mock_alt_client = MagicMock()
        mock_get_alt_client.return_value = mock_alt_client

        # Test with OpenAI provider
        response = structure_chat_completion(
            output_schema=dict,
            messages=[{"role": "user", "content": "Hello"}],
            model_key="openai:gpt-3",
        )
        self.assertIsInstance(response, ParsedChatCompletion)
        mock_openai_client.beta.chat.completions.parse.assert_called_once_with(
            temperature=0,
            model="gpt-3",
            messages=[{"role": "user", "content": "Hello"}],
            response_format=dict,
        )

        # Test with alternative provider
        mock_alt_client.beta.chat.completions.parse.return_value = MagicMock(
            spec=ParsedChatCompletion
        )
        response = structure_chat_completion(
            output_schema=dict,
            messages=[{"role": "user", "content": "Hello"}],
            model_key="deepseek:model",
        )
        self.assertIsInstance(response, ParsedChatCompletion)
        mock_get_alt_client.assert_called_once_with("deepseek:model")
        mock_alt_client.beta.chat.completions.parse.assert_called_once_with(
            temperature=0,
            model="model",
            messages=[{"role": "user", "content": "Hello"}],
            response_format=dict,
        )

    @patch("fluctlight.open.chat.chat_complete")
    def test_simple_assistant(self, mock_chat_complete):
        mock_completion = MagicMock(spec=ChatCompletion)
        mock_completion.choices = [MagicMock()]
        mock_completion.choices[0].message.content = "Hello, how can I help you?"
        mock_chat_complete.return_value = mock_completion

        response = simple_assistant(prompt="Hello", model_key="4o")
        self.assertEqual(response, "Hello, how can I help you?")
        mock_chat_complete.assert_called_once_with(
            model_key="4o",
            messages=[
                {"role": "system", "content": "You are a helpful assistant"},
                {"role": "user", "content": "Hello"},
            ],
        )

    @patch("fluctlight.open.chat.structure_chat_completion")
    def test_structure_simple_assistant(self, mock_structure_chat_completion):
        mock_parsed_completion = MagicMock(spec=ParsedChatCompletion)
        mock_parsed_completion.choices = [MagicMock()]
        mock_parsed_completion.choices[0].message.parsed = {
            "response": "Hello, how can I help you?"
        }
        mock_structure_chat_completion.return_value = mock_parsed_completion

        response = structure_simple_assistant(
            prompt="Hello", output_schema=dict, model_key="4o-mini"
        )
        self.assertEqual(response, {"response": "Hello, how can I help you?"})
        mock_structure_chat_completion.assert_called_once_with(
            output_schema=dict,
            messages=[
                {
                    "role": "system",
                    "content": "Assist user with the task with structure output",
                },
                {"role": "user", "content": "Hello"},
            ],
            model_key="4o-mini",
        )


if __name__ == "__main__":
    unittest.main()
