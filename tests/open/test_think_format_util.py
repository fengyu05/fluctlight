from fluctlight.open.think_format_util import extract_think_message
import unittest


class TestThinkFormatUtil(unittest.TestCase):
    def test_extract_think_message(self):
        # Test no think tags
        self.assertEqual(extract_think_message("hello world"), ["hello world"])

        # Test valid think tags
        self.assertEqual(extract_think_message("<think>abc</think>xyz"), ["abc", "xyz"])

        # Test multiple think tags (should take first one)
        self.assertEqual(
            extract_think_message("<think>first</think>middle<think>second</think>"),
            ["first", "middle<think>second</think>"],
        )

        # Test malformed tags
        self.assertEqual(
            extract_think_message("<think>incomplete"), ["<think>incomplete"]
        )

        # Test empty think content
        self.assertEqual(extract_think_message("<think></think>rest"), ["", "rest"])

        # Test whitespace handling
        self.assertEqual(
            extract_think_message("<think> abc \n</think> xyz "), ["abc", "xyz"]
        )


if __name__ == "__main__":
    unittest.main()
