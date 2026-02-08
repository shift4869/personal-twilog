import sys
import unittest
from collections import namedtuple
from datetime import datetime
from pathlib import Path

import freezegun
from mock import MagicMock, call, patch

from personal_twilog.memo_writer import MemoWriter
from personal_twilog.util import Result


class TestMemoWriter(unittest.TestCase):
    def setUp(self):
        self.enterContext(patch("personal_twilog.memo_writer.logger"))

    def _get_instance(self) -> MemoWriter:
        mock_orjson = self.enterContext(patch("personal_twilog.memo_writer.orjson"))
        self.enterContext(freezegun.freeze_time("2026-02-09T01:00:00"))

        mock_orjson.loads.return_value = {"memo_writer": {"vault_base_path": "./tests", "status": "enable"}}
        instance = MemoWriter()
        instance.is_enable = True
        return instance

    def test_init(self):
        instance = self._get_instance()
        self.assertEqual(Path("./tests"), instance.vault_base_path)
        self.assertEqual(datetime.now(), instance.now_date)
        self.assertEqual(datetime.now().strftime("%Y-%m-%d"), instance.now_date_str)
        self.assertEqual(datetime.now().strftime("%Y%m"), instance.year_month)
        self.assertEqual(
            Path("./tests") / "diary" / datetime.now().strftime("%Y%m") / f"{datetime.now().strftime('%Y-%m-%d')}.md",
            instance.dst_path,
        )
        self.assertTrue(instance.is_enable)

    def test_write(self):
        Params = namedtuple("Params", ["is_enable", "kind_exist_sentence", "memo", "result"])
        marker = MemoWriter.INSERT_TARGET_MARKER

        def pre_run(params: Params) -> MemoWriter:
            instance = self._get_instance()
            instance.is_enable = params.is_enable

            instance.dst_path = MagicMock()
            if params.kind_exist_sentence == "normal_sentence":
                instance.dst_path.read_text.return_value = f"{marker}already text\n"
            elif params.kind_exist_sentence == "non_newline":
                instance.dst_path.read_text.return_value = f"{marker}already text\nblock"
            elif params.kind_exist_sentence == "dupelicate":
                instance.dst_path.read_text.return_value = f"{marker}already text\n{params.memo}"
            elif params.kind_exist_sentence == "no_hit":
                instance.dst_path.read_text.return_value = f"marker no hit"
            return instance

        def post_run(actual: Result, instance: MemoWriter, params: Params) -> None:
            self.assertEqual(actual, params.result)
            if params.kind_exist_sentence == "normal_sentence":
                self.assertEqual(
                    [
                        call.read_text(encoding="utf-8"),
                        call.write_text(f"{marker}already text\n{params.memo}\n", encoding="utf-8"),
                    ],
                    instance.dst_path.mock_calls,
                )
            elif params.kind_exist_sentence == "non_newline":
                self.assertEqual(
                    [
                        call.read_text(encoding="utf-8"),
                        call.write_text(f"{marker}already text\nblock\n{params.memo}\n", encoding="utf-8"),
                    ],
                    instance.dst_path.mock_calls,
                )
            elif params.kind_exist_sentence in ["dupelicate", "no_hit"]:
                self.assertEqual(
                    [
                        call.read_text(encoding="utf-8"),
                    ],
                    instance.dst_path.mock_calls,
                )
            elif params.kind_exist_sentence == "disable":
                instance.dst_path.assert_not_called()

        params_list = [
            Params(True, "normal_sentence", "memo_sample", Result.success),
            Params(True, "non_newline", "memo_sample", Result.success),
            Params(True, "dupelicate", "memo_sample", Result.success),
            Params(True, "no_hit", "memo_sample", Result.failed),
            Params(False, "disable", "memo_sample", Result.failed),
        ]
        for params in params_list:
            instance = pre_run(params)
            actual = instance.write(params.memo)
            post_run(actual, instance, params)

    def test_search_and_write(self):
        Params = namedtuple("Params", ["is_enable", "kind_tweet_dict_list", "result"])
        marker = MemoWriter.INSERT_TARGET_MARKER

        def pre_run(params: Params) -> tuple[MemoWriter, list[dict]]:
            tweet_dict_list = []
            instance = self._get_instance()
            instance.is_enable = params.is_enable

            instance.write = MagicMock()
            now_date_str = datetime.now().strftime("%Y-%m-%d")
            marker = "メモ："
            if params.kind_tweet_dict_list == "include_memo":
                tweet_dict_list = [{"tweet_text": f"{marker}include_memo", "created_at": now_date_str}]
            elif params.kind_tweet_dict_list == "exclude_memo":
                tweet_dict_list = [{"tweet_text": f"exclude_memo", "created_at": now_date_str}]
            return instance, tweet_dict_list

        def post_run(actual: Result, instance: MemoWriter, params: Params) -> None:
            self.assertEqual(actual, params.result)
            if not params.is_enable:
                instance.write.assert_not_called()

            if params.kind_tweet_dict_list == "include_memo":
                instance.write.assert_called_once_with("include_memo")
            elif params.kind_tweet_dict_list == "exclude_memo":
                instance.write.assert_not_called()

        params_list = [
            Params(True, "include_memo", Result.success),
            Params(True, "exclude_memo", Result.success),
            Params(False, "", Result.success),
        ]
        for params in params_list:
            instance, tweet_dict_list = pre_run(params)
            actual = instance.search_and_write(tweet_dict_list)
            post_run(actual, instance, params)


if __name__ == "__main__":
    if sys.argv:
        del sys.argv[1:]
    unittest.main(warnings="ignore")
