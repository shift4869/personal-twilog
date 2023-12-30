import shutil
import sys
import unittest
from pathlib import Path

import orjson
from mock import patch

from personaltwilog.load_twitter_archive import ArchivedTweet, main, table_name
from personaltwilog.util import Result


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
        mock_create_engine = self.enterContext(patch("personaltwilog.load_twitter_archive.create_engine"))
        mock_base = self.enterContext(patch("personaltwilog.load_twitter_archive.Base"))
        mock_session = self.enterContext(patch("personaltwilog.load_twitter_archive.sessionmaker"))
        mock_glob = self.enterContext(patch("personaltwilog.load_twitter_archive.Path.glob"))
        mock_tqdm = self.enterContext(patch("personaltwilog.load_twitter_archive.tqdm"))
        mock_print = self.enterContext(patch("personaltwilog.load_twitter_archive.print"))

        mock_tqdm.side_effect = lambda any_list, desc: any_list

        input_json_file = "archived_tweets_sample.json"
        input_js_path = Path("./tests/cache/data") / "tweets.js"
        input_base_path = Path("./tests/cache/")
        output_db_path = Path(":memory:")

        input_js_path.parent.mkdir(exist_ok=True, parents=True)
        shutil.rmtree(input_js_path.parent)
        input_js_path.parent.mkdir(exist_ok=True, parents=True)
        shutil.copy2(input_base_path / input_json_file, input_js_path.parent)
        (input_js_path.parent / input_json_file).rename(input_js_path)

        actual = main(input_base_path, output_db_path)
        self.assertEqual(Result.SUCCESS, actual)

        shutil.rmtree(input_js_path.parent)
        pass


if __name__ == "__main__":
    if sys.argv:
        del sys.argv[1:]
    unittest.main(warnings="ignore")
