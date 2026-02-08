import re
import sys
import unittest
from pathlib import Path

import orjson
from mock import patch

from personal_twilog.parser.metric_parser import MetricParser
from personal_twilog.util import find_values


class TestMetricParser(unittest.TestCase):
    def get_json_dict(self) -> dict:
        return orjson.loads(Path("./tests/cache/timeline_sample.json").read_bytes())

    def get_instance(self) -> MetricParser:
        timeline_dict = self.get_json_dict()
        entry_list: list[dict] = find_values(timeline_dict, "entries")
        tweet_dict_list: list[dict] = find_values(entry_list, "tweet_results")
        registered_at = "2026-02-08T01:00:00"
        target_screen_name = "screen_name_1"
        parser = MetricParser(tweet_dict_list, registered_at, target_screen_name)
        return parser

    def test_init(self):
        target_screen_name = "screen_name_1"
        actual = self.get_instance()
        self.assertEqual(target_screen_name, actual.target_screen_name)

    def test_parse(self):
        instance = self.get_instance()

        def parse() -> list[dict]:
            flattened_tweet_list = instance._flatten(instance.tweet_dict_list)

            metric_dict = {}
            flattened_tweet_list.reverse()
            for tweet in flattened_tweet_list:
                user_dict: dict = tweet.get("core", {}).get("user_results", {}).get("result", {})
                if not user_dict:
                    continue
                user_legacy: dict = user_dict.get("legacy", {})
                screen_name: str = user_dict.get("core", {}).get("screen_name", "")
                if instance.target_screen_name != screen_name:
                    continue
                metric_dict = {
                    "screen_name": screen_name,
                    "status_count": user_legacy["statuses_count"],
                    "favorite_count": user_legacy["favourites_count"],
                    "media_count": user_legacy["media_count"],
                    "following_count": user_legacy["friends_count"],
                    "followers_count": user_legacy["followers_count"],
                    "registered_at": instance.registered_at,
                }
                break
            return [metric_dict] if metric_dict else []

        actual = instance.parse()
        expect = parse()
        self.assertNotEqual([], actual)
        self.assertEqual(expect, actual)

        instance.tweet_dict_list = []
        actual = instance.parse()
        expect = []
        self.assertEqual(expect, actual)


if __name__ == "__main__":
    if sys.argv:
        del sys.argv[1:]
    unittest.main(warnings="ignore")
