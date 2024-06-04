import re
import sys
import unittest
from pathlib import Path

import orjson

from personal_twilog.parser.likes_parser import LikesParser
from personal_twilog.util import find_values


class TestLikesParser(unittest.TestCase):
    def get_json_dict(self) -> dict:
        return orjson.loads(Path("./tests/cache/timeline_sample.json").read_bytes())

    def get_instance(self) -> LikesParser:
        timeline_dict = self.get_json_dict()
        entry_list: list[dict] = find_values(timeline_dict, "entries")
        tweet_dict_list: list[dict] = find_values(entry_list, "tweet_results")
        registered_at = "2023-10-07T01:00:00"
        user_id: str = "11111"
        user_name: str = "user_name_1"
        screen_name: str = "screen_name_1"
        parser = LikesParser(tweet_dict_list, registered_at, user_id, user_name, screen_name)
        return parser

    def test_init(self):
        timeline_dict = self.get_json_dict()
        entry_list: list[dict] = find_values(timeline_dict, "entries")
        expect: list[dict] = find_values(entry_list, "tweet_results")

        actual = self.get_instance()
        self.assertEqual(expect, actual.tweet_dict_list)
        self.assertEqual(expect, actual.result)
        self.assertEqual("2023-10-07T01:00:00", actual.registered_at)
        self.assertEqual("11111", actual.user_id)
        self.assertEqual("user_name_1", actual.user_name)
        self.assertEqual("screen_name_1", actual.screen_name)

    def test_parse(self):
        parser = self.get_instance()
        timeline_dict = self.get_json_dict()
        entry_list: list[dict] = find_values(timeline_dict, "entries")
        tweet_results: list[dict] = find_values(entry_list, "tweet_results")

        def parse() -> list[dict]:
            flattened_tweet_list = parser._flatten(tweet_results)
            tweet_dict_list = []
            for tweet in flattened_tweet_list:
                if not tweet:
                    continue
                tweet_legacy: dict = tweet["legacy"]
                tweet_user: dict = tweet["core"]["user_results"]["result"]
                tweet_user_legacy: dict = tweet_user["legacy"]

                tweet_id: str = tweet["rest_id"]
                tweet_text: str = tweet_legacy["full_text"]
                via_html: str = tweet["source"]
                tweet_via = re.findall("^<.+?>([^<]*?)<.+?>$", via_html)[0]
                user_id: str = tweet_user["rest_id"]
                user_name: str = tweet_user_legacy["name"]
                screen_name: str = tweet_user_legacy["screen_name"]
                tweet_url: str = f"https://twitter.com/{screen_name}/status/{tweet_id}"

                retweet_tweet, quote_tweet = parser._match_rt_quote(tweet)
                is_retweet: bool = bool(retweet_tweet != {})
                is_quote: bool = bool(quote_tweet != {})
                retweet_tweet_id = retweet_tweet.get("rest_id", "")
                quote_tweet_id = quote_tweet.get("rest_id", "")

                has_media = False
                extended_entities: dict = tweet_legacy.get("extended_entities", {})
                media_list = extended_entities.get("media", [])
                for media in media_list:
                    if parser._match_media(media):
                        has_media = True
                        break

                has_external_link = False
                entities: dict = tweet_legacy.get("entities", {})
                expanded_urls = parser._match_entities(entities).get("expanded_urls", [])
                if expanded_urls:
                    has_external_link = True

                created_at = parser._get_created_at(tweet)
                appeared_at = tweet["appeared_at"]
                tweet_dict = {
                    "tweet_id": tweet_id,
                    "tweet_text": tweet_text,
                    "tweet_via": tweet_via,
                    "tweet_url": tweet_url,
                    "tweet_user_id": user_id,
                    "tweet_user_name": user_name,
                    "tweet_screen_name": screen_name,
                    "user_id": parser.user_id,
                    "user_name": parser.user_name,
                    "screen_name": parser.screen_name,
                    "is_retweet": is_retweet,
                    "retweet_tweet_id": retweet_tweet_id,
                    "is_quote": is_quote,
                    "quote_tweet_id": quote_tweet_id,
                    "has_media": has_media,
                    "has_external_link": has_external_link,
                    "created_at": created_at,
                    "appeared_at": appeared_at,
                    "registered_at": parser.registered_at,
                }
                tweet_dict_list.append(tweet_dict)

            tweet_dict_list = parser._remove_duplicates(tweet_dict_list)
            tweet_dict_list.reverse()
            return tweet_dict_list

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
