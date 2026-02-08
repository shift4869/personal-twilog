import shutil
import sys
import unittest
from collections import namedtuple
from pathlib import Path

import orjson
from mock import patch

from personal_twilog.load_twitter_archive import ArchivedTweet, main, table_name
from personal_twilog.util import Result


class TestLoadTwitterArchive(unittest.TestCase):
    def test_table_name(self):
        table_name_pattern = "^TweetArchive_(.*)$"
        self.assertRegex(table_name, table_name_pattern)

    def test_ArchivedTweet(self):
        # init
        instance = ArchivedTweet(
            "tweet_id",
            "tweet_text",
            "tweet_via",
            "tweet_url",
            "user_id",
            "user_name",
            "screen_name",
            "is_retweet",
            "retweet_tweet_id",
            "is_quote",
            "quote_tweet_id",
            "has_media",
            "has_external_link",
            "created_at",
            "appeared_at",
            "registered_at",
        )
        self.assertEqual(None, instance.id)
        self.assertEqual("tweet_id", instance.tweet_id)
        self.assertEqual("tweet_text", instance.tweet_text)
        self.assertEqual("tweet_via", instance.tweet_via)
        self.assertEqual("tweet_url", instance.tweet_url)
        self.assertEqual("user_id", instance.user_id)
        self.assertEqual("user_name", instance.user_name)
        self.assertEqual("screen_name", instance.screen_name)
        self.assertEqual("is_retweet", instance.is_retweet)
        self.assertEqual("retweet_tweet_id", instance.retweet_tweet_id)
        self.assertEqual("is_quote", instance.is_quote)
        self.assertEqual("quote_tweet_id", instance.quote_tweet_id)
        self.assertEqual("has_media", instance.has_media)
        self.assertEqual("has_external_link", instance.has_external_link)
        self.assertEqual("created_at", instance.created_at)
        self.assertEqual("appeared_at", instance.appeared_at)
        self.assertEqual("registered_at", instance.registered_at)

        table_name_pattern = "^TweetArchive_(.*)$"
        self.assertRegex(ArchivedTweet.__tablename__, table_name_pattern)

        # create
        all_str = Path("./tests/cache/archived_tweets_sample.json").read_text("utf8")
        all_str = all_str.replace(f"window.YTD.tweets.part0 = ", "")
        json_dict = orjson.loads(all_str.encode())
        for entry in json_dict:
            instance = ArchivedTweet.create(entry)
            self.assertIsInstance(instance, ArchivedTweet)

    def test_main(self):
        mock_create_engine = self.enterContext(patch("personal_twilog.load_twitter_archive.create_engine"))
        mock_base = self.enterContext(patch("personal_twilog.load_twitter_archive.Base"))
        mock_session = self.enterContext(patch("personal_twilog.load_twitter_archive.sessionmaker"))
        mock_glob = self.enterContext(patch("personal_twilog.load_twitter_archive.Path.glob"))
        mock_tqdm = self.enterContext(patch("personal_twilog.load_twitter_archive.tqdm"))
        mock_print = self.enterContext(patch("personal_twilog.load_twitter_archive.print"))

        mock_tqdm.side_effect = lambda any_list, desc: any_list

        Params = namedtuple("Params", ["kind", "result"])

        def pre_run(params: Params) -> tuple[Path, Path]:
            ref_archived_json_path = Path("./tests/cache") / "archived_tweets_sample.json"
            input_path = Path("./tests/cache/archive/data") / "tweets.js"
            output_db_path = Path("./tests/cache/archive/data") / "archived_tweets_test.db"

            input_path.parent.mkdir(exist_ok=True, parents=True)
            shutil.rmtree(input_path.parent.parent)
            input_path.parent.mkdir(exist_ok=True, parents=True)

            if params.kind == "normal":
                # 正常系
                output_db_path.touch()
                shutil.copy2(ref_archived_json_path, input_path.parent)
                (input_path.parent / ref_archived_json_path.name).rename(input_path)
                return input_path.parent.parent, output_db_path
            elif params.kind == "predict_path":
                # 正常系（展開ディレクトリ重複吸収）
                shutil.rmtree(input_path.parent.parent)
                input_path = input_path.parent.parent / "archive" / "data" / input_path.name
                input_path.parent.mkdir(exist_ok=True, parents=True)

                output_db_path = input_path.parent / output_db_path.name
                output_db_path.touch()

                shutil.copy2(ref_archived_json_path, input_path.parent)
                (input_path.parent / ref_archived_json_path.name).rename(input_path)
                input_path = input_path.parent
                return input_path.parent.parent, output_db_path
            elif params.kind == "not_exist_js":
                # "tweets.js" が存在しない
                output_db_path.touch()
                shutil.copy2(ref_archived_json_path, input_path.parent)
                (input_path.parent / ref_archived_json_path.name).rename(input_path.parent / "invalid.js")
                return input_path.parent.parent, output_db_path
            elif params.kind == "invalid_dir":
                # ディレクトリ構造が不正
                shutil.rmtree(input_path.parent.parent)
                input_path = input_path.parent.parent / "invalid" / "data" / input_path.name
                input_path.parent.mkdir(exist_ok=True, parents=True)

                output_db_path = input_path.parent / output_db_path.name
                output_db_path.touch()

                shutil.copy2(ref_archived_json_path, input_path.parent)
                (input_path.parent / ref_archived_json_path.name).rename(input_path)
                input_path = input_path.parent
                return input_path.parent.parent, output_db_path
            elif params.kind == "not_exist_output_path":
                # 出力DBパスが不正
                # output_db_path.touch()  # 出力DBを作成しない
                return input_path.parent.parent, output_db_path
            elif params.kind == "not_exist_input_path":
                # 入力ディレクトリパスが不正
                return input_path, output_db_path
            elif params.kind == "invalid_type":
                # 引数の型が不正
                return "invalid_path", "invalid_path"

        def post_run(actual: Result, params: Params) -> None:
            self.assertEqual(params.result, actual)

        params_list = [
            Params("normal", Result.success),
            Params("predict_path", Result.success),
            Params("not_exist_js", Result.failed),
            Params("invalid_dir", Result.failed),
            Params("not_exist_output_path", Result.failed),
            Params("not_exist_input_path", Result.failed),
            Params("invalid_type", Result.failed),
        ]
        for params in params_list:
            input_base_path, output_db_path = pre_run(params)
            actual = main(input_base_path, output_db_path)
            post_run(actual, params)

        # 対象.jsファイルが存在しなかった
        # shutil.rmtree(input_js_path.parent)
        # input_js_path.parent.mkdir(exist_ok=True, parents=True)
        # output_db_path.touch()

        # actual = main(input_base_path, output_db_path)
        # self.assertEqual(Result.failed, actual)

        cache_archive_path = Path("./tests/cache/archive")
        cache_archive_path.parent.mkdir(exist_ok=True, parents=True)
        shutil.rmtree(cache_archive_path)


if __name__ == "__main__":
    if sys.argv:
        del sys.argv[1:]
    unittest.main(warnings="ignore")
