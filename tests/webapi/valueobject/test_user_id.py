import sys
import unittest

from personal_twilog.webapi.valueobject.user_id import UserId


class TestUserId(unittest.TestCase):
    def test_init(self):
        user_id = 123
        actual = UserId(user_id)
        self.assertEqual(user_id, actual.id)
        self.assertEqual(str(user_id), actual.id_str)

        with self.assertRaises(TypeError):
            actual = UserId("invalid_id")
        with self.assertRaises(ValueError):
            actual = UserId(-1)


if __name__ == "__main__":
    if sys.argv:
        del sys.argv[1:]
    unittest.main(warnings="ignore")
