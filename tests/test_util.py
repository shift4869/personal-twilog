import sys
import unittest
from pathlib import Path

import orjson

from personal_twilog.util import Result, find_values


class TestUtil(unittest.TestCase):
    def test_Result(self):
        self.assertEqual(True, hasattr(Result, "success"))
        self.assertEqual(True, hasattr(Result, "failed"))

    def _make_sample_dict(self) -> dict:
        return [
            {
                "result": {
                    "core": {"user_results": {"username": f"user{i}_username"}},
                    "legacy": {"user_results": {"username": f"legacyuser{i}_username"}},
                    "rest_id": f"rest_id{i}",
                }
            }
            for i in range(5)
        ]

    def test_find_values(self):
        sample_dict = self._make_sample_dict()

        # 辞書とキーのみ指定
        actual = find_values(sample_dict, "username")
        expect = [
            "user0_username",
            "legacyuser0_username",
            "user1_username",
            "legacyuser1_username",
            "user2_username",
            "legacyuser2_username",
            "user3_username",
            "legacyuser3_username",
            "user4_username",
            "legacyuser4_username",
        ]
        self.assertEqual(expect, actual)

        # ホワイトリスト指定
        actual = find_values(sample_dict, "username", False, ["result", "core", "user_results"])
        expect = [
            "user0_username",
            "user1_username",
            "user2_username",
            "user3_username",
            "user4_username",
        ]
        self.assertEqual(expect, actual)

        # ブラックリスト指定
        actual = find_values(sample_dict, "username", False, [], ["core"])
        expect = [
            "legacyuser0_username",
            "legacyuser1_username",
            "legacyuser2_username",
            "legacyuser3_username",
            "legacyuser4_username",
        ]
        self.assertEqual(expect, actual)

        # 一意に確定する想定
        actual = find_values(sample_dict[0], "rest_id", True)
        expect = "rest_id0"
        self.assertEqual(expect, actual)

        # 直下を調べる
        actual = find_values(sample_dict[0], "result", True, [""])
        expect = sample_dict[0]["result"]
        self.assertEqual(expect, actual)

        # 存在しないキーを指定
        actual = find_values(sample_dict, "invalid_key")
        expect = []
        self.assertEqual(expect, actual)

        # 空辞書を探索
        actual = find_values({}, "username")
        expect = []
        self.assertEqual(expect, actual)

        # 空リストを探索
        actual = find_values([], "username")
        expect = []
        self.assertEqual(expect, actual)

        # 文字列を指定
        actual = find_values("invalid_object", "username")
        expect = []
        self.assertEqual(expect, actual)

        # 一意に確定する想定の指定だが、複数見つかった場合
        with self.assertRaises(ValueError):
            actual = find_values(sample_dict, "username", True)

        # 一意に確定する想定の指定だが、見つからなかった場合
        with self.assertRaises(ValueError):
            actual = find_values(sample_dict, "invalid_key", True)


if __name__ == "__main__":
    if sys.argv:
        del sys.argv[1:]
    unittest.main(warnings="ignore")
