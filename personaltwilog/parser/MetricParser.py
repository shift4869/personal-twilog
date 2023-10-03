import logging.config
from copy import deepcopy
from datetime import datetime
from logging import INFO, getLogger
from pathlib import Path

import orjson

from personaltwilog.parser.ParserBase import ParserBase
from personaltwilog.Util import find_values

logger = getLogger(__name__)
logger.setLevel(INFO)


class MetricParser(ParserBase):
    def __init__(self, tweet_dict_list: list[dict], registered_at: str, target_screen_name: str) -> None:
        super().__init__(tweet_dict_list, registered_at)
        self.target_screen_name = target_screen_name

    def parse(self) -> list[dict]:
        flattened_tweet_list = self._flatten(self.tweet_dict_list)

        metric_dict = {}
        flattened_tweet_list_r = deepcopy(flattened_tweet_list)
        flattened_tweet_list_r.reverse()
        for tweet in flattened_tweet_list_r:
            user_dict: dict = tweet.get("core", {}) \
                                   .get("user_results", {}) \
                                   .get("result", {})
            if not user_dict:
                continue
            user_legacy: dict = user_dict.get("legacy", {})
            if self.target_screen_name != user_legacy.get("screen_name"):
                continue
            metric_dict = {
                "screen_name": user_legacy["screen_name"],
                "status_count": user_legacy["statuses_count"],
                "favorite_count": user_legacy["favourites_count"],
                "media_count": user_legacy["media_count"],
                "following_count": user_legacy["friends_count"],
                "followers_count": user_legacy["followers_count"],
                "registered_at": self.registered_at,
            }
            break
        return [metric_dict] if metric_dict else []


if __name__ == "__main__":
    logging.config.fileConfig("./log/logging.ini", disable_existing_loggers=False)
    for name in logging.root.manager.loggerDict:
        if "personaltwilog" in name:
            continue
        if "__main__" in name:
            continue
        getLogger(name).disabled = True

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

    parser = MetricParser(
        tweet_list,
        datetime.now().replace(microsecond=0).isoformat(),
        "_shift4869"
    )
    dict_list = parser.parse()
    print(len(dict_list))
