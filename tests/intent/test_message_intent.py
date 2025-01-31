import unittest

from fluctlight.intent.message_intent import (
    MessageIntent,
    create_intent,
    get_message_intent_by_text,
    has_emoji_variants,
)


class TestMessageIntent(unittest.TestCase):
    def test_uppercase_key(self):
        intent = MessageIntent(key="testKey")
        self.assertEqual(intent.key, "TESTKEY")

    def test_equal_wo_metadata(self):
        intent1 = MessageIntent(key="somekey", metadata={"some": "data2"})
        intent2 = MessageIntent(key="SomeKey", metadata={"some": "data"})
        self.assertTrue(intent1.equal_wo_metadata(intent2))

        intent3 = MessageIntent(key="otherkey")
        self.assertFalse(intent1.equal_wo_metadata(intent3))

    def test_create_intent_with_default(self):
        intent = create_intent("test")
        self.assertEqual(intent.key, "TEST")

    def test_create_intent_unknown(self):
        intent = create_intent(unknown=True)
        self.assertEqual(intent.key, "")
        self.assertTrue(intent.unknown)

    def test_get_message_intent_by_emoji_found(self):
        intent = get_message_intent_by_text(":cat:")
        self.assertEqual(intent.key, "MIAO")

    def test_get_message_intent_by_emoji_not_found(self):
        intent = get_message_intent_by_text(":dog:")
        self.assertEqual(intent.key, "")
        self.assertTrue(intent.unknown)

    def test_has_emoji_variants(self):
        self.assertTrue(has_emoji_variants("REASON", ":reason: hello"))
        self.assertTrue(has_emoji_variants("REASON", ":thinking_face: test"))
        self.assertTrue(has_emoji_variants("SEARCH", ":web: query"))
        self.assertFalse(has_emoji_variants("REASON", "no emoji here"))
        self.assertFalse(has_emoji_variants("INVALID", ":reason:"))


if __name__ == "__main__":
    unittest.main()
