import os
import unittest
from unittest.mock import patch, MagicMock
from fluctlight.open.alternatives import (
    get_alternative_platforms,
    Alternative,
    get_alt_client,
    get_alt_client_from_model_key,
    _CLIENT_CACHE,
)


class TestGetAlternativePlatforms(unittest.TestCase):
    @patch.dict(
        os.environ,
        {
            "OPENAI_ALTERNATES": "DEEPSEEK,FIREWORKS,HYSP",
            "DEEPSEEK_API_KEY": "sk-55122367b95941ba946c22c62a547823",
            "DEEPSEEK_BASE_URL": "https://api.deepseek.com",
            "FIREWORKS_API_KEY": "fw_3ZXQrYd83H5514maFd6QM4Fh",
            "FIREWORKS_BASE_URL": "https://api.fireworkweb.com",
            "HYSP_API_KEY": "sk-8f7b71d4165865780eb9cd25f9eb769b9d36694df35ef16e",
            "HYSP_BASE_URL": "https://local-llm.hysp.org",
        },
    )
    def test_get_alternative_platforms(self):
        expected = {
            "DEEPSEEK": Alternative(
                api_key="sk-55122367b95941ba946c22c62a547823",
                base_url="https://api.deepseek.com",
            ),
            "FIREWORKS": Alternative(
                api_key="fw_3ZXQrYd83H5514maFd6QM4Fh",
                base_url="https://api.fireworkweb.com",
            ),
            "HYSP": Alternative(
                api_key="sk-8f7b71d4165865780eb9cd25f9eb769b9d36694df35ef16e",
                base_url="https://local-llm.hysp.org",
            ),
        }
        result = get_alternative_platforms()
        self.assertEqual(result, expected)

    @patch("fluctlight.open.alternatives.get_alternative_platforms")
    @patch("fluctlight.open.alternatives.make_openai_client")
    @patch("fluctlight.open.alternatives.TEST_MODE", True)
    def test_get_alt_client(
        self, mock_make_openai_client, mock_get_alternative_platforms
    ):
        mock_get_alternative_platforms.return_value = {
            "DEEPSEEK": MagicMock(
                api_key="sk-55122367b95941ba946c22c62a547823",
                base_url="https://api.deepseek.com",
            )
        }
        mock_client = MagicMock()
        mock_make_openai_client.return_value = mock_client

        # Clear the cache before testing
        _CLIENT_CACHE.clear()

        client = get_alt_client("DEEPSEEK")
        self.assertEqual(client, mock_client)
        mock_make_openai_client.assert_called_once_with(
            api_key="sk-55122367b95941ba946c22c62a547823",
            base_url="https://api.deepseek.com",
            use_langsmith_wrapper=False,
        )

        # Test cache
        client_cached = get_alt_client("DEEPSEEK")
        self.assertEqual(client_cached, mock_client)
        mock_make_openai_client.assert_called_once()  # Ensure it's only called once

    @patch("fluctlight.open.alternatives.get_alt_client")
    def test_get_alt_client_from_model_key(self, mock_get_alt_client):
        mock_client = MagicMock()
        mock_get_alt_client.return_value = mock_client

        client = get_alt_client_from_model_key("DEEPSEEK:model")
        self.assertEqual(client, mock_client)
        mock_get_alt_client.assert_called_once_with("DEEPSEEK")


if __name__ == "__main__":
    unittest.main()
