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

    def test_get_message_intent_by_emoji_with_annotation_search(self):
        intent = get_message_intent_by_text(":cat: :search:")
        self.assertTrue(intent.search)
        self.assertFalse(intent.reason)

    def test_get_message_intent_by_emoji_with_annotation_reason(self):
        intent = get_message_intent_by_text(":cat: :reason:")
        self.assertTrue(intent.reason)
        self.assertFalse(intent.search)

    def test_has_emoji_variants(self):
        self.assertTrue(has_emoji_variants("REASON", ":reason: hello"))
        self.assertTrue(has_emoji_variants("REASON", ":thinking_face: test"))
        self.assertTrue(has_emoji_variants("SEARCH", ":web: query"))
        self.assertFalse(has_emoji_variants("REASON", "no emoji here"))
        self.assertFalse(has_emoji_variants("INVALID", ":reason:"))


if __name__ == "__main__":
    unittest.main()
