import re
from datetime import datetime
from pathlib import Path

import orjson

from personaltwilog.parser.parser_base import ParserBase
from personaltwilog.util import find_values


class MediaParser(ParserBase):
    def __init__(self, tweet_dict_list: list[dict], registered_at: str) -> None:
        super().__init__(tweet_dict_list, registered_at)

    def parse(self) -> list[dict]:
        """flattened_tweet_list を解釈して DB の Media テーブルに投入するための list[dict] を返す"""
        flattened_tweet_list = self._flatten(self.tweet_dict_list)
        media_dict_list = []
        for tweet in flattened_tweet_list:
            if not tweet:
                continue

            tweet_legacy: dict = tweet["legacy"]

            # tweet がメディアを持つかどうか
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

            created_at = self._get_created_at(tweet)
            appeared_at = tweet["appeared_at"]

            for media in media_list:
                media_info = self._match_media(media)
                if not media_info:
                    continue

                media_filename = media_info["media_filename"]
                media_url = media_info["media_url"]
                media_thumbnail_url = media_info["media_thumbnail_url"]
                media_type = media_info["media_type"]
                media_size = self._get_media_size(media_url)

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
                    "registered_at": self.registered_at,
                }
                media_dict_list.append(media_dict)

        media_dict_list = self._remove_duplicates(media_dict_list)
        media_dict_list.reverse()
        return media_dict_list


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

    parser = MediaParser(tweet_list, datetime.now().replace(microsecond=0).isoformat())
    dict_list = parser.parse()
    print(len(dict_list))
