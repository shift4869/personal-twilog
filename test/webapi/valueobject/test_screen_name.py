import sys
import unittest

from personaltwilog.webapi.valueobject.ScreenName import ScreenName


class TestScreenName(unittest.TestCase):
    def test_init(self):
        pattern = "^[0-9a-zA-Z_]+$"
        screen_name = "dummy_screen_name"
        actual = ScreenName(screen_name)
        self.assertEqual(screen_name, actual.name)
        self.assertEqual(pattern, actual.PATTERN)

        with self.assertRaises(ValueError):
            actual = ScreenName("不正なスクリーンネーム")
        with self.assertRaises(TypeError):
            actual = ScreenName(-1)


if __name__ == "__main__":
    if sys.argv:
        del sys.argv[1:]
    unittest.main(warnings="ignore")
