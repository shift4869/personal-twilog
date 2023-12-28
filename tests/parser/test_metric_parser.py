import sys
import unittest
from copy import deepcopy
from pathlib import Path

import orjson

from personaltwilog.parser.metric_parser import MetricParser
from personaltwilog.util import find_values


class TestMetricParser(unittest.TestCase):
    def get_json_dict(self) -> dict:
        return orjson.loads(Path("./tests/cache/timeline_sample.json").read_bytes())

    def get_instance(self) -> MetricParser:
        timeline_dict = self.get_json_dict()
        entry_list: list[dict] = find_values(timeline_dict, "entries")
        tweet_dict_list: list[dict] = find_values(entry_list, "tweet_results")
        registered_at = "2023-10-07T01:00:00"
        target_screen_name = "screen_name_1"
        parser = MetricParser(tweet_dict_list, registered_at, target_screen_name)
        return parser

    def test_init(self):
        timeline_dict = self.get_json_dict()
        entry_list: list[dict] = find_values(timeline_dict, "entries")
        expect: list[dict] = find_values(entry_list, "tweet_results")

        actual = self.get_instance()
        self.assertEqual(expect, actual.tweet_dict_list)
        self.assertEqual(expect, actual.result)
        self.assertEqual("2023-10-07T01:00:00", actual.registered_at)
        self.assertEqual("screen_name_1", actual.target_screen_name)

    def test_parse(self):
        parser = self.get_instance()
        timeline_dict = self.get_json_dict()
        entry_list: list[dict] = find_values(timeline_dict, "entries")
        tweet_results: list[dict] = find_values(entry_list, "tweet_results")

        def parse() -> list[dict]:
            flattened_tweet_list = parser._flatten(tweet_results)

            metric_dict = {}
            flattened_tweet_list_r = deepcopy(flattened_tweet_list)
            flattened_tweet_list_r.reverse()
            for tweet in flattened_tweet_list_r:
                user_dict: dict = tweet.get("core", {}).get("user_results", {}).get("result", {})
                if not user_dict:
                    continue
                user_legacy: dict = user_dict.get("legacy", {})
                if parser.target_screen_name != user_legacy.get("screen_name"):
                    continue
                metric_dict = {
                    "screen_name": user_legacy["screen_name"],
                    "status_count": user_legacy["statuses_count"],
                    "favorite_count": user_legacy["favourites_count"],
                    "media_count": user_legacy["media_count"],
                    "following_count": user_legacy["friends_count"],
                    "followers_count": user_legacy["followers_count"],
                    "registered_at": parser.registered_at,
                }
                break
            return [metric_dict] if metric_dict else []

        actual = parser.parse()
        expect = parse()
        self.assertNotEqual([], actual)
        self.assertEqual(expect, actual)

        parser.tweet_dict_list = []
        actual = parser.parse()
        expect = []
        self.assertEqual(expect, actual)


if __name__ == "__main__":
    if sys.argv:
        del sys.argv[1:]
    unittest.main(warnings="ignore")
