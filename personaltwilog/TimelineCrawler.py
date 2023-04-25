# coding: utf-8
import configparser
import json
import logging.config
import pprint
import re
import sys
import urllib.parse
from datetime import datetime, timedelta
from logging import INFO, getLogger
from pathlib import Path
from time import sleep
from typing import Literal

from personaltwilog.db.Model import Tweet
from personaltwilog.db.TweetDB import TweetDB
from personaltwilog.webapi.TwitterAPI import TwitterAPI

logger = getLogger(__name__)
logger.setLevel(INFO)


class TimelineCrawler():
    def __init__(self) -> None:
        config = configparser.ConfigParser()
        CONFIG_FILE_NAME = "./config/config.ini"
        if not config.read(CONFIG_FILE_NAME, encoding="utf8"):
            raise IOError

        self.config = config
        self.screen_name = config["twitter"]["screen_name"]
        # self.twitter = TwitterAPI(self.screen_name)
        self.tweet_db = TweetDB()

    def _match_media(self, media: dict) -> dict:
        """mediaから保存対象のメディアURLを取得する

        Args:
            media_dict (dict): tweet.legacy.extended_entities.media[] の要素

        Returns:
            result (dict): 成功時 result, そうでなければ空辞書
        """
        match media:
            case {
                "type": "photo",
                "media_url_https": media_url,
            }:
                media_filename = Path(media_url).name
                media_thumbnail_url = media_url + ":large"
                media_url = media_url + ":orig"
                result = {
                    "media_filename": media_filename,
                    "media_url": media_url,
                    "media_thumbnail_url": media_thumbnail_url,
                }
                return result
            case {
                "type": "video" | "animated_gif",
                "video_info": {"variants": video_variants},
                "media_url_https": media_thumbnail_url,
            }:
                media_url = ""
                bitrate = -sys.maxsize  # 最小値
                for video_variant in video_variants:
                    if video_variant["content_type"] == "video/mp4":
                        if int(video_variant["bitrate"]) > bitrate:
                            # 同じ動画の中で一番ビットレートが高い動画を保存する
                            media_url = video_variant["url"]
                            bitrate = int(video_variant["bitrate"])
                # クエリを除去
                url_path = Path(urllib.parse.urlparse(media_url).path)
                media_url = urllib.parse.urljoin(media_url, url_path.name)
                media_filename = Path(media_url).name
                media_thumbnail_url = media_thumbnail_url + ":orig"
                result = {
                    "media_filename": media_filename,
                    "media_url": media_url,
                    "media_thumbnail_url": media_thumbnail_url,
                }
                return result
        return {}

    def _match_rt_quote(self, tweet: dict) -> tuple[dict, dict]:
        """tweet に含まれる RT と QT の tweet 辞書を探索する

        Args:
            tweet (dict): RT と QT が含まれうる tweet 辞書

        Returns:
            tuple[dict, dict]:
                (retweet_tweet, quote_tweet)
                それぞれ RT と QT の tweet 辞書
                tweet が RT と QT を保持していなかった場合はそれぞれ空辞書を返す
        """
        if not isinstance(tweet, dict):
            raise TypeError("Argument tweet is not dict.")

        retweet_tweet = {}
        quote_tweet = {}

        # RTしているツイートの場合
        match tweet:
            case {
                "legacy": {
                    "retweeted": True,
                    "retweeted_status_result": {
                        "result": tweet_result,
                    },
                },
            }:
                retweet_tweet = tweet_result

        # 引用RTしているツイートの場合
        match tweet:
            case {
                "legacy": {
                    "is_quote_status": True,
                },
                "quoted_status_result": {
                    "result": tweet_result,
                },
            }:
                quote_tweet = tweet_result

        # 引用RTをRTしている場合
        match tweet:
            case {
                "legacy": {
                    "retweeted": True,
                    "retweeted_status_result": {
                        "result": {
                            "rest_id": _,
                            "quoted_status_result": {
                                "result": quote_tweet_result,
                            },
                        },
                    },
                },
            }:
                retweet_tweet = tweet.get("legacy", {}) \
                                     .get("retweeted_status_result", {}) \
                                     .get("result")
                quote_tweet = quote_tweet_result
        return (retweet_tweet, quote_tweet)

    def _get_created_at(self, tweet: dict) -> str:
        """tweet に含まれる created_at を返す
        """
        if not isinstance(tweet, dict):
            raise TypeError("Argument tweet is not dict.")

        created_at_str = ""
        match tweet:
            case {
                "legacy": {
                    "created_at": created_at_tweet_str,
                }
            }:
                created_at_str = created_at_tweet_str
            case _:
                ValueError("Argument tweet.legacy.created_at is not exist.")

        td_format = "%a %b %d %H:%M:%S +0000 %Y"
        created_at_gmt = datetime.strptime(created_at_str, td_format)
        created_at_jst = created_at_gmt + timedelta(hours=9)
        created_at = created_at_jst.isoformat()
        return created_at

    def _flatten(self, tweet_list: list[dict]) -> list[dict]:
        """tweet_list を平滑化する

            ここでの"平滑化"とは tweet_list に含まれる
            RT と QT の tweet 辞書を元の tweet と同じ階層のリストに格納することを指す
            元のツイート, RT先ツイート, QT先ツイート があるため、
            1つのツイートは最大で3レコードに増える
            このメソッドの返り値は、RT と QT の階層を気にせずに
            線形探索ができることが保証される

        Args:
            tweet_list (list[dict]):
                RT と QT が含まれうる tweet 辞書のリスト
                それぞれの要素のルートは、"result" キーを含む

        Returns:
            list[dict]: 元のツイート, RT先ツイート, QT先ツイート が1階層に格納された tweet 辞書
        """
        flattened_tweet_list = []
        for tweet in tweet_list:
            tweet = tweet.get("result", {})
            retweet_tweet, quote_tweet = self._match_rt_quote(tweet)

            # 元ツイートの appeared_at は created_at と同じ
            appeared_at = self._get_created_at(tweet)
            tweet["appeared_at"] = appeared_at

            # 元ツイート格納
            flattened_tweet_list.append(tweet)

            if retweet_tweet:
                # RT先ツイートがあるならば格納
                # 元ツイートの created_at を
                # RT の appeared_at とする
                retweet_tweet["appeared_at"] = appeared_at
                flattened_tweet_list.append(retweet_tweet)
            if quote_tweet:
                # QT先ツイートがあるならば格納
                # 元ツイートの created_at を
                # QT の appeared_at とする
                quote_tweet["appeared_at"] = appeared_at
                flattened_tweet_list.append(quote_tweet)
        return flattened_tweet_list

    def _interporate(self, tweet_list: list[dict]) -> list[dict]:
        """tweet_list を解釈してDBに投入する
        """
        # 平滑化
        flattened_tweet_list = self._flatten(tweet_list)

        registered_at = datetime.now().replace(microsecond=0).isoformat()
        tweet_dict_list = []
        for tweet in flattened_tweet_list:
            if not tweet:
                continue
            tweet_legacy: dict = tweet.get("legacy")
            tweet_user: dict = tweet.get("core", {}).get("user_results", {}).get("result")
            tweet_user_legacy: dict = tweet_user.get("legacy")

            tweet_id: str = tweet.get("rest_id")
            tweet_text: str = tweet_legacy.get("full_text")
            via_html: str = tweet.get("source")
            tweet_via = re.findall("^<.+?>([^<]*?)<.+?>$", via_html)[0]
            user_id: str = tweet_user.get("rest_id")
            user_name: str = tweet_user_legacy.get("name")
            screen_name: str = tweet_user_legacy.get("screen_name")
            tweet_url: str = f"https://twitter.com/{screen_name}/status/{tweet_id}"

            retweet_tweet, quote_tweet = self._match_rt_quote(tweet)
            is_retweet: bool = bool(retweet_tweet != {})
            is_quote: bool = bool(quote_tweet != {})
            retweet_tweet_id = retweet_tweet.get("rest_id", "")
            quote_tweet_id = quote_tweet.get("rest_id", "")

            # tweet がメディアを持つかどうか
            extended_entities: dict = tweet_legacy.get("extended_entities", {})
            media_list = extended_entities.get("media", [])
            has_media = False
            for media in media_list:
                if self._match_media(media):
                    has_media = True
                    break

            # tweet が外部リンクを持つかどうか
            # TODO:: linksearch に任せる
            has_external_link = False
            entities: dict = tweet_legacy.get("entities", {})
            if entities:
                urls = entities.get("urls", [""])
                if len(urls) > 0 and urls[0] != "":
                    has_external_link = True

            created_at = self._get_created_at(tweet)
            appeared_at = tweet.get("appeared_at")
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
                "registered_at": registered_at,
            }
            tweet_dict_list.append(tweet_dict)
        return tweet_dict_list

    def run(self):
        # 探索する id_str の下限値を設定
        min_id = self.tweet_db.select_for_max_id()

        # TL取得
        limit = 300
        tweet_list = []
        # tweet_list = self.twitter.get_user_timeline(self.screen_name, limit, min_id)
        # tweet_list = tweet_list[:-1]
        # with Path("./tweet_list_response.txt").open("w") as fout:
        #     json.dump(tweet_list, fout, indent=4)
        with Path("./tweet_list_response.txt").open("r") as fout:
            tweet_list = json.load(fout)

        # 返り値を解釈してDBに格納する
        tweet_dict_list = self._interporate(tweet_list)

        # 重複排除
        seen = []
        tweet_dict_list = [
            tweet_dict for tweet_dict in tweet_dict_list
            if (tweet_id := tweet_dict.get("tweet_id", "")) != "" and (tweet_id not in seen) and (not seen.append(tweet_id))
        ]

        # ソート順調整
        tweet_dict_list.reverse()
        self.tweet_db.upsert(tweet_dict_list)
        return []


if __name__ == "__main__":
    logging.config.fileConfig("./log/logging.ini", disable_existing_loggers=False)
    for name in logging.root.manager.loggerDict:
        if "personaltwilog" not in name:
            getLogger(name).disabled = True

    crawler = TimelineCrawler()
    crawler.run()
