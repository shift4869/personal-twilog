import sys
import unittest

from personal_twilog.webapi.valueobject.user_name import UserName


class TestUserName(unittest.TestCase):
    def test_init(self):
        user_name = "dummy_username"
        actual = UserName(user_name)
        self.assertEqual(user_name, actual.name)

        with self.assertRaises(TypeError):
            actual = UserName(-1)


if __name__ == "__main__":
    if sys.argv:
        del sys.argv[1:]
    unittest.main(warnings="ignore")
