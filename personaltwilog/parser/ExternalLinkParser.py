import re
from datetime import datetime
from pathlib import Path

import orjson

from personaltwilog.parser.ParserBase import ParserBase
from personaltwilog.Util import find_values


class ExternalLinkParser(ParserBase):
    def __init__(self, tweet_dict_list: list[dict], registered_at: str) -> None:
        super().__init__(tweet_dict_list, registered_at)

    def parse(self) -> list[dict]:
        flattened_tweet_list = self._flatten(self.tweet_dict_list)
        external_link_dict_list = []
        for tweet in flattened_tweet_list:
            if not tweet:
                continue

            tweet_legacy: dict = tweet["legacy"]

            # tweet が外部リンクを持つかどうか
            entities: dict = tweet_legacy.get("entities", {})
            expanded_urls = self._match_entities(entities).get("expanded_urls", [])
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

            created_at = self._get_created_at(tweet)
            appeared_at = tweet["appeared_at"]

            for expanded_url in expanded_urls:
                external_link_url = expanded_url
                external_link_type = self._get_external_link_type(external_link_url)
                external_link_dict = {
                    "tweet_id": tweet_id,
                    "tweet_text": tweet_text,
                    "tweet_via": tweet_via,
                    "tweet_url": tweet_url,
                    "external_link_url": external_link_url,
                    "external_link_type": external_link_type,
                    "created_at": created_at,
                    "appeared_at": appeared_at,
                    "registered_at": self.registered_at,
                }
                external_link_dict_list.append(external_link_dict)

        external_link_dict_list = self._remove_duplicates(external_link_dict_list)
        external_link_dict_list.reverse()
        return external_link_dict_list


if __name__ == "__main__":
    data_cache_path = Path("./data/175674367/")
    cache_path = list(data_cache_path.glob("*UserTweetsAndReplies*"))[-1]
    tweet_dict = orjson.loads(cache_path.read_bytes())
    entry_list: list[dict] = find_values(tweet_dict, "entries")
    tweet_results: list[dict] = find_values(entry_list, "tweet_results")

    tweet_list = []
    for data_dict in tweet_results:
        if t := data_dict.get("result", {}).get("tweet", {}):
            data_dict: dict = {"result": t}
        if data_dict:
            tweet_list.append(data_dict)

    parser = ExternalLinkParser(tweet_list, datetime.now().replace(microsecond=0).isoformat())
    dict_list = parser.parse()
    print(len(dict_list))
