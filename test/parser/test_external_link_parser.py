import re
import sys
import unittest
from pathlib import Path

import orjson

from personaltwilog.parser.ExternalLinkParser import ExternalLinkParser
from personaltwilog.Util import find_values


class TestExternalLinkParser(unittest.TestCase):
    def get_json_dict(self) -> dict:
        return orjson.loads(Path("./test/cache/timeline_sample.json").read_bytes())

    def get_instance(self) -> ExternalLinkParser:
        timeline_dict = self.get_json_dict()
        entry_list: list[dict] = find_values(timeline_dict, "entries")
        tweet_dict_list: list[dict] = find_values(entry_list, "tweet_results")
        registered_at = "2023-10-07T01:00:00"
        parser = ExternalLinkParser(tweet_dict_list, registered_at)
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
            external_link_dict_list = []
            for tweet in flattened_tweet_list:
                if not tweet:
                    continue
                tweet_legacy: dict = tweet["legacy"]

                entities: dict = tweet_legacy.get("entities", {})
                expanded_urls = parser._match_entities(entities).get("expanded_urls", [])
                if not expanded_urls:
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

                for expanded_url in expanded_urls:
                    external_link_url = expanded_url
                    external_link_type = parser._get_external_link_type(external_link_url)
                    external_link_dict = {
                        "tweet_id": tweet_id,
                        "tweet_text": tweet_text,
                        "tweet_via": tweet_via,
                        "tweet_url": tweet_url,
                        "external_link_url": external_link_url,
                        "external_link_type": external_link_type,
                        "created_at": created_at,
                        "appeared_at": appeared_at,
                        "registered_at": parser.registered_at,
                    }
                    external_link_dict_list.append(external_link_dict)

            external_link_dict_list = parser._remove_duplicates(external_link_dict_list)
            external_link_dict_list.reverse()
            return external_link_dict_list

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
