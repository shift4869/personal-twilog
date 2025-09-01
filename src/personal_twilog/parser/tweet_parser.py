import re
from datetime import datetime
from logging import INFO, getLogger
from pathlib import Path

import orjson

from personal_twilog.parser.parser_base import ParserBase
from personal_twilog.util import find_value, find_values

logger = getLogger(__name__)
logger.setLevel(INFO)


class TweetParser(ParserBase):
    def __init__(self, tweet_dict_list: list[dict], registered_at: str) -> None:
        super().__init__(tweet_dict_list, registered_at)

    def parse(self) -> list[dict]:
        """tweet_list を解釈してDBに投入する"""
        flattened_tweet_list: list[dict] = self._flatten(self.tweet_dict_list)
        tweet_dict_list: list[dict] = []
        for tweet in flattened_tweet_list:
            if not tweet:
                continue
            tweet_legacy: dict = find_value(tweet, ["legacy"])
            tweet_user: dict = find_value(tweet, ["core", "user_results", "result"])
            # tweet_user_legacy: dict = tweet_user["legacy"]

            if not all([tweet_legacy, tweet_user]):
                msg = "tweet_legacy, tweet_user"
                logger.warning(f"fetched tweet structure is invalid: {msg}.")
                continue

            tweet_id: str = find_value(tweet, ["rest_id"])
            tweet_text: str = find_value(tweet_legacy, ["full_text"])
            user_id: str = find_value(tweet_user, ["rest_id"])
            user_name: str = find_value(tweet_user, ["core", "name"])
            screen_name: str = find_value(tweet_user, ["core", "screen_name"])
            tweet_url: str = f"https://twitter.com/{screen_name}/status/{tweet_id}"

            if not all([tweet_id, tweet_text, user_id, user_name, screen_name, tweet_url]):
                msg = "tweet_id, tweet_text, user_id, user_name, screen_name, tweet_url"
                logger.warning(f"fetched tweet structure is invalid: {msg}.")
                continue

            via_html: str = find_value(tweet, ["source"])
            tweet_via: str = found[0] if (found := re.findall("^<.+?>([^<]*?)<.+?>$", via_html)) else ""

            if not tweet_via:
                logger.warning(f"fetched tweet structure is invalid: tweet_via.")
                continue

            # rt, qt があるかどうか
            retweet_tweet, quote_tweet = self._match_rt_quote(tweet)
            is_retweet: bool = bool(retweet_tweet != {})
            is_quote: bool = bool(quote_tweet != {})
            retweet_tweet_id: str = find_value(retweet_tweet, ["rest_id"])
            quote_tweet_id: str = find_value(quote_tweet, ["rest_id"])

            # tweet がメディアを持つかどうか
            has_media = False
            media_list: list[dict] = find_value(tweet_legacy, ["extended_entities", "media"], [])
            for media in media_list:
                if self._match_media(media):
                    has_media = True
                    break

            # tweet が外部リンクを持つかどうか
            has_external_link = False
            entities: dict = find_value(tweet_legacy, ["entities"], {})
            expanded_urls: list[dict] = find_value(self._match_entities(entities), ["expanded_urls"], [])
            if expanded_urls:
                has_external_link = True

            created_at: str = self._get_created_at(tweet)
            appeared_at: str = find_value(tweet, ["appeared_at"])
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
    data_cache_path = Path("./data/")
    cache_path = data_cache_path / "get_user_tweets.json"
    tweet_results = orjson.loads(cache_path.read_bytes())

    tweet_list = []
    for data_dict in tweet_results:
        if t := data_dict.get("result", {}).get("tweet", {}):
            data_dict: dict = {"result": t}
        if data_dict:
            tweet_list.append(data_dict)

    parser = TweetParser(tweet_list, datetime.now().replace(microsecond=0).isoformat())
    tweet_dict_list = parser.parse()
    print(len(tweet_dict_list))
