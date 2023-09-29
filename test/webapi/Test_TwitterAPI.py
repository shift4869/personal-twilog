import sys
import unittest
from contextlib import ExitStack

from mock import MagicMock, patch

from personaltwilog.webapi.TwitterAPI import TwitterAPI
from personaltwilog.webapi.valueobject.ScreenName import ScreenName
from personaltwilog.webapi.valueobject.Token import Token
from personaltwilog.webapi.valueobject.UserId import UserId


class TestTwitterAPI(unittest.TestCase):
    def test_init(self):
        authorize_screen_name = "authorize_screen_name"
        ct0 = "ct0"
        auth_token = "auth_token"
        actual = TwitterAPI(authorize_screen_name, ct0, auth_token)
        self.assertEqual(ScreenName(authorize_screen_name), actual.authorize_screen_name)
        self.assertEqual(Token.create(authorize_screen_name, ct0, auth_token), actual.token)

    def test_get_userid(self):
        pass

    def test_find_values(self):
        pass

    def test_get_likes(self):
        with ExitStack() as stack:
            # mockcp = stack.enter_context(patch("configparser.ConfigParser"))
            pass

    def test_get_user_timeline(self):
        pass


if __name__ == "__main__":
    if sys.argv:
        del sys.argv[1:]
    unittest.main(warnings="ignore")
