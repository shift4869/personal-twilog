import sys
import unittest

from personal_twilog.webapi.valueobject.screen_name import ScreenName
from personal_twilog.webapi.valueobject.token import Token


class TestToken(unittest.TestCase):
    def test_init(self):
        screen_name = ScreenName("dummy_screen_name")
        ct0 = "dummy_ct0"
        auth_token = "dummy_auth_token"
        actual = Token(screen_name, ct0, auth_token)
        self.assertEqual(screen_name, actual.screen_name)
        self.assertEqual(ct0, actual.ct0)
        self.assertEqual(auth_token, actual.auth_token)

        with self.assertRaises(TypeError):
            actual = Token(-1, ct0, auth_token)
        with self.assertRaises(TypeError):
            actual = Token(screen_name, -1, auth_token)
        with self.assertRaises(TypeError):
            actual = Token(screen_name, ct0, -1)

    def test_create(self):
        screen_name = "dummy_screen_name"
        ct0 = "dummy_ct0"
        auth_token = "dummy_auth_token"
        actual = Token.create(screen_name, ct0, auth_token)
        self.assertEqual(ScreenName(screen_name), actual.screen_name)
        self.assertEqual(ct0, actual.ct0)
        self.assertEqual(auth_token, actual.auth_token)

        actual = Token.create(ScreenName(screen_name), ct0, auth_token)
        self.assertEqual(ScreenName(screen_name), actual.screen_name)
        self.assertEqual(ct0, actual.ct0)
        self.assertEqual(auth_token, actual.auth_token)

        with self.assertRaises(TypeError):
            actual = Token.create(-1, ct0, auth_token)
        with self.assertRaises(TypeError):
            actual = Token.create(screen_name, -1, auth_token)
        with self.assertRaises(TypeError):
            actual = Token.create(screen_name, ct0, -1)


if __name__ == "__main__":
    if sys.argv:
        del sys.argv[1:]
    unittest.main(warnings="ignore")
