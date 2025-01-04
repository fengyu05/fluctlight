import unittest
from unittest.mock import patch

from fluctlight.utt.config import _TRUTHY_VALUES, config_default_bool


class TestConfigDefaultBool(unittest.TestCase):
    @patch("os.environ.get")
    def test_truthy_values(self, mock_get):
        # Mock various truthy values
        for value in _TRUTHY_VALUES:
            mock_get.return_value = value
            self.assertTrue(config_default_bool("ANY_KEY"))

    @patch("os.environ.get")
    def test_falsy_values(self, mock_get):
        # Test non-truthy values
        falsy_values = ["false", "0", "no", "n", "f", "", None, "randomstring"]
        for value in falsy_values:
            mock_get.return_value = value
            self.assertFalse(config_default_bool("ANY_KEY"))

    def test_default_value(self):
        self.assertTrue(
            config_default_bool("ANY_KEY", default_value=True)
        )  # Default is True


if __name__ == "__main__":
    unittest.main()
