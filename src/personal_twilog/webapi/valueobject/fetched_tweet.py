from typing import Self

from personal_twilog.util import find_value, find_values


class FetchedTweet:
    tweet_id: str
    tweet_text: str
    tweet_via: str
    tweet_url: str
    user_id: str
    user_name: str
    screen_name: str
    is_retweet: str
    retweet_tweet_id: str
    is_quote: str
    quote_tweet_id: str
    has_media: str
    has_external_link: str
    created_at: str
    appeared_at: str
    registered_at: str

    def __post_init__(self, tweet_dict: dict) -> None:
        match tweet_dict:
            case {
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
                "registered_at": registered_at,
            }:
                self.tweet_id = tweet_id
                self.tweet_text = tweet_text
                self.tweet_via = tweet_via
                self.tweet_url = tweet_url
                self.user_id = user_id
                self.user_name = user_name
                self.screen_name = screen_name
                self.is_retweet = is_retweet
                self.retweet_tweet_id = retweet_tweet_id
                self.is_quote = is_quote
                self.quote_tweet_id = quote_tweet_id
                self.has_media = has_media
                self.has_external_link = has_external_link
                self.created_at = created_at
                self.appeared_at = appeared_at
                self.registered_at = registered_at
            case _:
                raise ValueError("tweet_dict is invalid dict structure.")

    @classmethod
    def create(cls, tweet_dict: dict) -> Self:
        pass


class FetchedTweetList:
    _list: list[FetchedTweet] = []

    def __post_init__(self, fetched_tweet_list: list[FetchedTweet]) -> None:
        if not isinstance(list, fetched_tweet_list):
            raise ValueError(f"fetched_tweet_list must be list.")
        if not all([isinstance(FetchedTweet, t) for t in fetched_tweet_list]):
            raise ValueError(f"fetched_tweet_list must be list[FetchedTweet].")
        self._list = fetched_tweet_list

    @classmethod
    def create(cls, tweet_list: list[dict]) -> Self:
        result = []
        for data_dict in tweet_list:
            result.append(FetchedTweet.create(data_dict))
        return FetchedTweetList(result)


if __name__ == "__main__":
    from pathlib import Path

    import orjson

    data_cache_path = Path("./data/")
    cache_path = data_cache_path / "get_user_tweets.json"
    tweet_dict = orjson.loads(cache_path.read_bytes())
    tweet_results: list[dict] = find_values(tweet_dict, "tweet_results")
    for tweet in tweet_results:
        key_path = ("result", "rest_id")
        tweet_id = find_value(tweet, key_path, {"error": "error1"})
        pass
    pass
