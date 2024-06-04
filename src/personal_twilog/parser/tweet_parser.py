import re
from datetime import datetime
from pathlib import Path

import orjson

from personal_twilog.parser.parser_base import ParserBase
from personal_twilog.util import find_values


class TweetParser(ParserBase):
    def __init__(self, tweet_dict_list: list[dict], registered_at: str) -> None:
        super().__init__(tweet_dict_list, registered_at)

    def parse(self) -> list[dict]:
        """tweet_list を解釈してDBに投入する"""
        flattened_tweet_list = self._flatten(self.tweet_dict_list)
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

            # rt, qt があるかどうか
            retweet_tweet, quote_tweet = self._match_rt_quote(tweet)
            is_retweet: bool = bool(retweet_tweet != {})
            is_quote: bool = bool(quote_tweet != {})
            retweet_tweet_id = retweet_tweet.get("rest_id", "")
            quote_tweet_id = quote_tweet.get("rest_id", "")

            # tweet がメディアを持つかどうか
            has_media = False
            extended_entities: dict = tweet_legacy.get("extended_entities", {})
            media_list = extended_entities.get("media", [])
            for media in media_list:
                if self._match_media(media):
                    has_media = True
                    break

            # tweet が外部リンクを持つかどうか
            has_external_link = False
            entities: dict = tweet_legacy.get("entities", {})
            expanded_urls = self._match_entities(entities).get("expanded_urls", [])
            if expanded_urls:
                has_external_link = True

            created_at = self._get_created_at(tweet)
            appeared_at = tweet["appeared_at"]
            tweet_dict = {
                "tweet_id": tweet_id,
                "tweet_text": tweet_text,
                "tweet_via": tweet_via,
                "tweet_url": tweet_url,
                "user_id": user_id,
                "user_name": user_name,
                "screen_name": screen_name,
                "is_retweet": is_retweet,
                "retweet_tweet_id": retweet_tweet_id,
                "is_quote": is_quote,
                "quote_tweet_id": quote_tweet_id,
                "has_media": has_media,
                "has_external_link": has_external_link,
                "created_at": created_at,
                "appeared_at": appeared_at,
                "registered_at": self.registered_at,
            }
            tweet_dict_list.append(tweet_dict)

        tweet_dict_list = self._remove_duplicates(tweet_dict_list)
        tweet_dict_list.reverse()
        return tweet_dict_list


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

    parser = TweetParser(tweet_list, datetime.now().replace(microsecond=0).isoformat())
    tweet_dict_list = parser.parse()
    print(len(tweet_dict_list))
