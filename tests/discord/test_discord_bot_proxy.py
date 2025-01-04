# pylint: disable=protected-access
import unittest
from unittest.mock import MagicMock
from discord.message import Message
from discord.user import User
from fluctlight.discord.discord_bot_proxy import DiscordBotProxy


class TestDiscordBotProxy(unittest.TestCase):
    def setUp(self):
        self.bot_proxy = DiscordBotProxy()
        self.bot_proxy.client = MagicMock()
        self.bot_proxy.client.user = MagicMock(spec=User)
        self.bot_proxy.client.user.id = 12345

    def test_should_reply_to_direct_message(self):
        message = MagicMock(spec=Message)
        message.author = MagicMock(spec=User)
        message.author.id = 67890
        message.channel = MagicMock()
        message.channel.__class__.__name__ = "DMChannel"
        message.content = "Hello"

        self.bot_proxy._bot_access_accept = MagicMock(return_value=True)
        self.bot_proxy._bot_has_reply = MagicMock(return_value=False)

        self.assertTrue(self.bot_proxy._should_reply(message))

    def test_should_not_reply_to_self_message(self):
        message = MagicMock(spec=Message)
        message.author = self.bot_proxy.client.user
        message.content = "Hello"

        self.assertFalse(self.bot_proxy._should_reply(message))

    def test_should_reply_when_mentioned(self):
        message = MagicMock(spec=Message)
        message.author = MagicMock(spec=User)
        message.author.id = 67890
        message.channel = MagicMock()
        message.channel.__class__.__name__ = "TextChannel"
        message.content = "Hello"
        self.bot_proxy.client.user.mentioned_in = MagicMock(return_value=True)
        self.bot_proxy._bot_access_accept = MagicMock(return_value=True)

        self.assertTrue(self.bot_proxy._should_reply(message))

    def test_bot_access_accept_all(self):
        message = MagicMock(spec=Message)
        message.channel = MagicMock()
        message.channel.__class__.__name__ = "DMChannel"

        self.assertTrue(self.bot_proxy._bot_access_accept(message, access_mode="all"))

    def test_bot_access_accept_none(self):
        message = MagicMock(spec=Message)
        message.channel = MagicMock()
        message.channel.__class__.__name__ = "DMChannel"
        self.assertFalse(self.bot_proxy._bot_access_accept(message, access_mode="none"))

    def test_bot_access_accept_no_member(self):
        message = MagicMock(spec=Message)
        message.channel = MagicMock()
        message.channel.__class__.__name__ = "DMChannel"

        self.bot_proxy.get_message_author_member = MagicMock(return_value=None)

        self.assertFalse(
            self.bot_proxy._bot_access_accept(message, access_mode="member")
        )

    def test_parse_access_role(self):
        access_mode = "role:admin,moderator"
        expected_roles = ["admin", "moderator"]
        self.assertEqual(self.bot_proxy.parse_access_role(access_mode), expected_roles)


if __name__ == "__main__":
    unittest.main()
