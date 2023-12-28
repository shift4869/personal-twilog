import re
import sys
import unittest
from contextlib import ExitStack
from pathlib import Path

import orjson
from mock import patch

from personaltwilog.parser.media_parser import MediaParser
from personaltwilog.util import find_values


class TestMediaParser(unittest.TestCase):
    def get_json_dict(self) -> dict:
        return orjson.loads(Path("./tests/cache/timeline_sample.json").read_bytes())

    def get_instance(self) -> MediaParser:
        timeline_dict = self.get_json_dict()
        entry_list: list[dict] = find_values(timeline_dict, "entries")
        tweet_dict_list: list[dict] = find_values(entry_list, "tweet_results")
        registered_at = "2023-10-07T01:00:00"
        parser = MediaParser(tweet_dict_list, registered_at)
        return parser

    def test_init(self):
        timeline_dict = self.get_json_dict()
        entry_list: list[dict] = find_values(timeline_dict, "entries")
        expect: list[dict] = find_values(entry_list, "tweet_results")

        actual = self.get_instance()
        self.assertEqual(expect, actual.tweet_dict_list)
        self.assertEqual(expect, actual.result)
        self.assertEqual("2023-10-07T01:00:00", actual.registered_at)

    def test_parse(self):
        parser = self.get_instance()
        timeline_dict = self.get_json_dict()
        entry_list: list[dict] = find_values(timeline_dict, "entries")
        tweet_results: list[dict] = find_values(entry_list, "tweet_results")

        def parse() -> list[dict]:
            flattened_tweet_list = parser._flatten(tweet_results)
            media_dict_list = []
            for tweet in flattened_tweet_list:
                if not tweet:
                    continue
                tweet_legacy: dict = tweet["legacy"]

                extended_entities: dict = tweet_legacy.get("extended_entities", {})
                media_list = extended_entities.get("media", [])
                if not media_list:
                    continue

                tweet_user: dict = tweet["core"]["user_results"]["result"]
                tweet_user_legacy: dict = tweet_user["legacy"]

                tweet_id: str = tweet["rest_id"]
                tweet_text: str = tweet_legacy["full_text"]
                via_html: str = tweet["source"]
                tweet_via = re.findall("^<.+?>([^<]*?)<.+?>$", via_html)[0]
                screen_name: str = tweet_user_legacy["screen_name"]
                tweet_url: str = f"https://twitter.com/{screen_name}/status/{tweet_id}"

                created_at = parser._get_created_at(tweet)
                appeared_at = tweet["appeared_at"]

                for media in media_list:
                    media_info = parser._match_media(media)
                    if not media_info:
                        continue

                    media_filename = media_info["media_filename"]
                    media_url = media_info["media_url"]
                    media_thumbnail_url = media_info["media_thumbnail_url"]
                    media_type = media_info["media_type"]
                    media_size = -1

                    media_dict = {
                        "tweet_id": tweet_id,
                        "tweet_text": tweet_text,
                        "tweet_via": tweet_via,
                        "tweet_url": tweet_url,
                        "media_filename": media_filename,
                        "media_url": media_url,
                        "media_thumbnail_url": media_thumbnail_url,
                        "media_type": media_type,
                        "media_size": media_size,
                        "created_at": created_at,
                        "appeared_at": appeared_at,
                        "registered_at": parser.registered_at,
                    }
                    media_dict_list.append(media_dict)

            media_dict_list = parser._remove_duplicates(media_dict_list)
            media_dict_list.reverse()
            return media_dict_list

        with ExitStack() as stack:
            mock_get_media_size = stack.enter_context(
                patch("personaltwilog.parser.media_parser.MediaParser._get_media_size")
            )
            mock_get_media_size.side_effect = lambda media_url: -1

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
