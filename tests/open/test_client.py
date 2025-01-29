import unittest
from httpx import URL
from unittest.mock import patch, MagicMock
from fluctlight.open.client import (
    make_openai_client,
    get_alternative_platforms,
    get_open_client,
    Alternative,
    OPENAI_CLIENT,
)


class TestOpenAIClient(unittest.TestCase):
    def test_make_openai_client(self):
        client = make_openai_client(api_key="test-key")
        self.assertEqual(client.api_key, "test-key")
        self.assertEqual(client.base_url, URL("https://api.openai.com/v1/"))

        client = make_openai_client(api_key="test-key", base_url="http://test.com")
        self.assertEqual(client.api_key, "test-key")
        self.assertEqual(client.base_url, "http://test.com")

    @patch("fluctlight.open.client.wrap_openai")
    def test_make_openai_client_with_langsmith(self, mock_wrap_openai):
        mock_wrapped_client = MagicMock()
        mock_wrap_openai.return_value = mock_wrapped_client

        client = make_openai_client(api_key="test-key", use_langsmith_wrapper=True)
        self.assertEqual(client, mock_wrapped_client)
        mock_wrap_openai.assert_called_once()

    @patch.dict(
        "os.environ",
        {
            "OPENAI_ALTERNATES": "DEEPSEEK,FIREWORKS",
            "DEEPSEEK_API_KEY": "test-key-1",
            "DEEPSEEK_BASE_URL": "http://deepseek.com",
            "FIREWORKS_API_KEY": "test-key-2",
            "FIREWORKS_BASE_URL": "http://fireworks.com",
        },
    )
    def test_get_alternative_platforms(self):
        platforms = get_alternative_platforms()
        self.assertEqual(len(platforms), 2)
        self.assertIn("deepseek", platforms)
        self.assertIn("fireworks", platforms)

        deepseek = platforms["deepseek"]
        self.assertEqual(deepseek.api_key, "test-key-1")
        self.assertEqual(deepseek.base_url, "http://deepseek.com")

    @patch.dict("os.environ", {"OPENAI_ALTERNATES": ""})
    def test_get_alternative_platforms_empty(self):
        platforms = get_alternative_platforms()
        self.assertEqual(len(platforms), 0)

    def test_get_open_client_openai(self):
        client = get_open_client("openai")
        self.assertEqual(client, OPENAI_CLIENT)

    @patch.dict("fluctlight.open.client._CLIENT_CACHE", {})
    @patch.dict(
        "fluctlight.open.client._ALT_PLATFORMS",
        {"deepseek": Alternative(api_key="test-key", base_url="http://test.com")},
    )
    def test_get_open_client_alternative(self):
        client1 = get_open_client("deepseek")
        client2 = get_open_client("deepseek")

        self.assertEqual(client1, client2)  # Test caching
        self.assertEqual(client1.api_key, "test-key")
        self.assertEqual(client1.base_url, "http://test.com")

    def test_get_open_client_unknown(self):
        with self.assertRaises(ValueError) as context:
            get_open_client("unknown")
        self.assertEqual(str(context.exception), "Unknown platform: unknown")


if __name__ == "__main__":
    unittest.main()
