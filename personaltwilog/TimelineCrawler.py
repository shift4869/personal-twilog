# coding: utf-8
import configparser
import copy
import json
import logging.config
import re
import sys
import urllib.parse
from datetime import datetime, timedelta
from logging import INFO, getLogger
from pathlib import Path

import orjson
import requests

from personaltwilog.db.ExternalLinkDB import ExternalLinkDB
from personaltwilog.db.LikesDB import LikesDB
from personaltwilog.db.MediaDB import MediaDB
from personaltwilog.db.MetricDB import MetricDB
from personaltwilog.db.TweetDB import TweetDB
from personaltwilog.webapi.TwitterAPI import TwitterAPI

logger = getLogger(__name__)
logger.setLevel(INFO)
DEBUG = False


class TimelineCrawler():
    CACHE_FILE_PATH = "./cache/timeline_response.txt"

    def __init__(self) -> None:
        logger.info("TimelineCrawler init -> start")
        CONFIG_FILE_NAME = "./config/config.json"
        config = orjson.loads(Path(CONFIG_FILE_NAME).read_bytes())

        config = config["twitter_api_client_list"][0]  # TODO::authorize複数対応
        self.config = config
        authorize_screen_name = config["authorize"]["screen_name"]
        ct0 = config["authorize"]["ct0"]
        auth_token = config["authorize"]["auth_token"]
        if not DEBUG:
            self.twitter = TwitterAPI(authorize_screen_name, ct0, auth_token)
        else:
            self.twitter = None
        self.tweet_db = TweetDB()
        self.likes_db = LikesDB()
        self.media_db = MediaDB()
        self.metric_db = MetricDB()
        self.external_link_db = ExternalLinkDB()

        # 各DBで共通に使う registered_at を取得
        self.registered_at = datetime.now().replace(microsecond=0).isoformat()
        logger.info("TimelineCrawler init -> done")

    def _get_external_link_type(self, external_link_url: str) -> str:
        url = external_link_url
        pattern = r"^https://www.pixiv.net/artworks/[0-9]+"
        if re.search(pattern, url):
            return "pixiv"
        pattern = r"^https://www.pixiv.net/novel/show.php\?id=[0-9]+"
        if re.search(pattern, url):
            return "pixiv_novel"
        pattern = r"^https?://nijie.info/view.php\?id=[0-9]+"
        if re.search(pattern, url):
            return "nijie"
        pattern = r"^https?://nijie.info/view_popup.php\?id=[0-9]+"
        if re.search(pattern, url):
            return "nijie"
        pattern = r"^https?://nijie.info/view_popup.php\?id=[0-9]+"
        if re.search(pattern, url):
            return "nijie"
        pattern = r"^https://seiga.nicovideo.jp/seiga/(im)[0-9]+"
        if re.search(pattern, url):
            return "nico_seiga"
        pattern = r"^http://nico.ms/(im)[0-9]+"
        if re.search(pattern, url):
            return "nico_seiga"
        pattern = r"^https://skeb.jp/\@(.+?)/works/([0-9]+)"
        if re.search(pattern, url):
            return "skeb"
        return ""

    def _match_entities(self, entities: dict) -> dict:
        """entities に含まれる expanded_url を収集するためのmatch

        Args:
            entities (dict): _match_entities_tweet.entities

        Returns:
            expanded_urls (dict): entities に含まれる expanded_url のみを抽出した辞書, 解析失敗時は空辞書
        """
        match entities:
            case {"urls": urls_dict}:
                expanded_urls = []
                for url_dict in urls_dict:
                    expanded_url = url_dict.get("expanded_url", "")
                    if not expanded_url:
                        continue
                    expanded_urls.append(expanded_url)
                return {"expanded_urls": expanded_urls}
        return {}

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
                    "media_type": media.get("type", "photo"),
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
                    "media_type": media.get("type", "video"),
                }
                return result
        return {}

    def _get_media_size(self, media_url: str) -> int:
        # HEADリクエストを送信してレスポンスヘッダーを取得
        response = requests.head(media_url)
        # Content-Lengthフィールドからファイルサイズを取得
        file_size = int(response.headers.get("Content-Length", 0))
        return file_size

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
                    "retweeted_status_result": {
                        "result": tweet_result,
                    },
                },
            }:
                retweet_tweet = tweet_result

        # 引用RTしているツイートの場合
        match tweet:
            case {
                "quoted_status_result": {
                    "result": tweet_result,
                },
            }:
                quote_tweet = tweet_result

        # 引用RTをRTしている場合
        match tweet:
            case {
                "legacy": {
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
                retweet_tweet_result = tweet.get("legacy", {}) \
                                            .get("retweeted_status_result", {}) \
                                            .get("result", {})
                retweet_tweet = retweet_tweet_result
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
                raise ValueError("Argument tweet.legacy.created_at is not exist.")

        td_format = "%a %b %d %H:%M:%S +0000 %Y"
        created_at_gmt = datetime.strptime(created_at_str, td_format)
        created_at_jst = created_at_gmt + timedelta(hours=9)
        created_at = created_at_jst.isoformat()
        return created_at

    def _flatten(self, tweet_list: list[dict]) -> list[dict]:
        """tweet_list を平滑化する

            ここでの"平滑化"とは tweet_list に含まれる
            RT と QT の tweet 辞書を元の tweet とともにリストに格納することを指す
            元のツイート, RT先ツイート, QT先ツイート があるため、
            1つのツイートは最大で3レコードに増える
            このメソッドの返り値は、RT と QT の階層を気にせずに
            線形探索ができることが保証される
            また appeared_at の項目もここで設定する

        Args:
            tweet_list (list[dict]):
                RT と QT が含まれうる tweet 辞書のリスト
                それぞれの要素のルートは、"result" キーを含む

        Returns:
            list[dict]: 元のツイート, RT先ツイート, QT先ツイート が1階層に格納された tweet 辞書
        """
        edited_tweet_list: list[dict] = []
        flattened_tweet_list: list[dict] = []
        for tweet in tweet_list:
            tweet = tweet.get("result", {})
            if tweet.get("__typename", "") == "TweetWithVisibilityResults":
                # 辞書構造が異なる場合がある？
                # 閲覧アカウントを制限しているツイート？
                tweet = tweet.get("tweet", {})
            if tweet.get("__typename", "") == "TweetTombstone":
                # 削除されたツイート
                continue
            # RT先ツイート, QT先ツイートを取得する
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

        # 構造チェックして、必要なら整合性をとる
        for tweet in flattened_tweet_list:
            if tweet.get("__typename", "") == "TweetWithVisibilityResults":
                appeared_at = tweet.get("appeared_at", "")
                tweet = tweet.get("tweet", {})
                tweet["appeared_at"] = appeared_at
            if tweet.get("__typename", "") == "TweetTombstone":
                # 削除されたツイート
                continue
            match tweet:
                case {
                    "core": {
                        "user_results": {
                            "result": {
                                "legacy": l1,
                            }
                        }
                    },
                    "legacy": l2,
                    "rest_id": rest_id,
                    "source": source,
                } if l1 != {} and l2 != {} and rest_id != "" and source != "":
                    pass
                case _:
                    raise ValueError("flatten failed. invalid '__typename' or structure.")
            edited_tweet_list.append(tweet)

        return edited_tweet_list

    def _interporate_to_tweet(self, flattened_tweet_list: list[dict]) -> list[dict]:
        """tweet_list を解釈してDBに投入する
        """
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
            has_media = False
            extended_entities: dict = tweet_legacy.get("extended_entities", {})
            media_list = extended_entities.get("media", [])
            for media in media_list:
                if self._match_media(media):
                    has_media = True
                    break

            # tweet が外部リンクを持つかどうか
            # TODO:: linksearch に任せる？
            has_external_link = False
            entities: dict = tweet_legacy.get("entities", {})
            expanded_urls = self._match_entities(entities).get("expanded_urls", [])
            if expanded_urls:
                has_external_link = True

            created_at = self._get_created_at(tweet)
            appeared_at = tweet.get("appeared_at", None)
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
        return tweet_dict_list

    def _interporate_to_media(self, flattened_tweet_list: list[dict]) -> list[dict]:
        """flattened_tweet_list を解釈して DB の Media テーブルに投入するための list[dict] を返す
        """
        media_dict_list = []
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
            screen_name: str = tweet_user_legacy.get("screen_name")
            tweet_url: str = f"https://twitter.com/{screen_name}/status/{tweet_id}"

            created_at = self._get_created_at(tweet)
            appeared_at = tweet.get("appeared_at", None)

            # tweet がメディアを持つかどうか
            extended_entities: dict = tweet_legacy.get("extended_entities", {})
            media_list = extended_entities.get("media", [])
            for media in media_list:
                media_info = self._match_media(media)
                if not media_info:
                    continue

                media_filename = media_info.get("media_filename")
                media_url = media_info.get("media_url")
                media_thumbnail_url = media_info.get("media_thumbnail_url")
                media_type = media_info.get("media_type")
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
        return media_dict_list

    def _interporate_to_external_link(self, flattened_tweet_list: list[dict]) -> list[dict]:
        """tweet_list を解釈してDBに投入する
        """
        external_link_dict_list = []
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
            screen_name: str = tweet_user_legacy.get("screen_name")
            tweet_url: str = f"https://twitter.com/{screen_name}/status/{tweet_id}"

            created_at = self._get_created_at(tweet)
            appeared_at = tweet.get("appeared_at", None)

            # tweet が外部リンクを持つかどうか
            # TODO:: linksearch に任せる？
            entities: dict = tweet_legacy.get("entities", {})
            expanded_urls = self._match_entities(entities).get("expanded_urls", [])
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
        return external_link_dict_list

    def _interporate_to_metric(self, flattened_tweet_list: list[dict], target_screen_name: str) -> list[dict]:
        """flattened_tweet_list を解釈して DB の Metric テーブルに投入するための list[dict] を返す
        """
        flattened_tweet_list_r = copy.deepcopy(flattened_tweet_list)
        flattened_tweet_list_r.reverse()
        for tweet in flattened_tweet_list_r:
            user_dict: dict = tweet.get("core", {}) \
                                   .get("user_results", {}) \
                                   .get("result", {})
            if not user_dict:
                continue
            user_legacy: dict = user_dict.get("legacy", {})
            if target_screen_name != user_legacy.get("screen_name"):
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
            return [metric_dict]
        return []

    def timeline_crawl(self, screen_name: str) -> list[dict]:
        logger.info("TimelineCrawler timeline_crawl -> start")
        logger.info("TimelineCrawler timeline_crawl init -> start")
        # 探索する id_str の下限値を設定
        min_id = self.tweet_db.select_for_max_id(screen_name)
        logger.info(f"Target timeline's screen_name is '{screen_name}'.")
        logger.info(f"Last registered tweet_id is '{min_id}'.")
        logger.info("TimelineCrawler timeline_crawl init -> done")

        # TL取得
        logger.info(f"Getting timeline of '{screen_name}' -> start")
        limit = 300
        tweet_list = []
        if self.twitter:
            tweet_list = self.twitter.get_user_timeline(screen_name, limit, min_id)
            tweet_list = tweet_list[:-1]
            if tweet_list:
                with Path(TimelineCrawler.CACHE_FILE_PATH).open("w", encoding="utf8") as fout:
                    json.dump(tweet_list, fout, indent=4, ensure_ascii=False)
        else:
            with Path(TimelineCrawler.CACHE_FILE_PATH).open("r", encoding="utf8") as fout:
                tweet_list = json.load(fout)

        if not tweet_list:
            logger.info(f"Getting timeline of '{screen_name}' -> done")
            logger.info(f"No new tweet of '{screen_name}'.")
            logger.info("TimelineCrawler timeline_crawl -> done")
            return []
        logger.info(f"Number of new tweet of '{screen_name}' is {len(tweet_list)}.")
        logger.info(f"Getting timeline of '{screen_name}' -> done")

        # 平滑化
        logger.info("Flattened -> start")
        flattened_tweet_list = self._flatten(tweet_list)
        logger.info("Flattened -> done")

        # Tweet
        logger.info("Tweet table update -> start")
        tweet_dict_list = self._interporate_to_tweet(flattened_tweet_list)
        seen = []
        tweet_dict_list = [
            tweet_dict for tweet_dict in tweet_dict_list
            if (tweet_id := tweet_dict.get("tweet_id", "")) != "" and (tweet_id not in seen) and (not seen.append(tweet_id))
        ]
        tweet_dict_list.reverse()
        self.tweet_db.upsert(tweet_dict_list)
        logger.info("Tweet table update -> done")

        # Media
        logger.info("Media table update -> start")
        media_dict_list = self._interporate_to_media(flattened_tweet_list)
        seen = []
        media_dict_list = [
            r for r in media_dict_list
            if (tweet_id := r.get("tweet_id", "")) != "" and (tweet_id not in seen) and (not seen.append(tweet_id))
        ]
        media_dict_list.reverse()
        self.media_db.upsert(media_dict_list)
        logger.info("Media table update -> done")

        # ExternalLink
        logger.info("ExternalLink table update -> start")
        external_link_dict_list = self._interporate_to_external_link(flattened_tweet_list)
        seen = []
        external_link_dict_list = [
            r for r in external_link_dict_list
            if (tweet_id := r.get("tweet_id", "")) != "" and (tweet_id not in seen) and (not seen.append(tweet_id))
        ]
        external_link_dict_list.reverse()
        self.external_link_db.upsert(external_link_dict_list)
        logger.info("ExternalLink table update -> done")

        # Metric
        logger.info("Metric table update -> start")
        metric_dict_list = self._interporate_to_metric(flattened_tweet_list, screen_name)
        self.metric_db.upsert(metric_dict_list)
        logger.info("Metric table update -> done")

        logger.info("TimelineCrawler timeline_crawl -> done")
        return flattened_tweet_list

    def likes_crawl(self, screen_name: str) -> list[dict]:
        logger.info("TimelineCrawler likes_crawl -> start")
        logger.info("TimelineCrawler likes_crawl init -> start")
        # 探索する id_str の下限値を設定
        min_id = self.likes_db.select_for_max_id()
        logger.info(f"Target Likes's screen_name is '{screen_name}'.")
        logger.info(f"Last registered tweet_id is '{min_id}'.")
        logger.info("TimelineCrawler likes_crawl init -> done")

        # Likes 取得
        logger.info(f"Getting Likes of '{screen_name}' -> start")
        limit = 300
        tweet_list = []
        if self.twitter:
            tweet_list = self.twitter.get_likes(screen_name, limit, min_id)
            tweet_list = tweet_list[:-1]
            if tweet_list:
                with Path(TimelineCrawler.CACHE_FILE_PATH).open("w", encoding="utf8") as fout:
                    json.dump(tweet_list, fout, indent=4, ensure_ascii=False)
        else:
            with Path(TimelineCrawler.CACHE_FILE_PATH).open("r", encoding="utf8") as fout:
                tweet_list = json.load(fout)

        if not tweet_list:
            logger.info(f"Getting Likes of '{screen_name}' -> done")
            logger.info(f"No new tweet of '{screen_name}'.")
            logger.info("TimelineCrawler likes_crawl -> done")
            return []
        logger.info(f"Number of new tweet of '{screen_name}' is {len(tweet_list)}.")
        logger.info(f"Getting Likes of '{screen_name}' -> done")

        # 平滑化
        logger.info("Flattened -> start")
        flattened_tweet_list = self._flatten(tweet_list)
        logger.info("Flattened -> done")

        # Likes
        logger.info("Likes table update -> start")
        tweet_dict_list = self._interporate_to_tweet(flattened_tweet_list)
        seen = []
        tweet_dict_list = [
            tweet_dict for tweet_dict in tweet_dict_list
            if (tweet_id := tweet_dict.get("tweet_id", "")) != "" and (tweet_id not in seen) and (not seen.append(tweet_id))
        ]
        tweet_dict_list.reverse()
        self.likes_db.upsert(tweet_dict_list)
        logger.info("Likes table update -> done")

        # Media
        logger.info("Media table update -> start")
        media_dict_list = self._interporate_to_media(flattened_tweet_list)
        seen = []
        media_dict_list = [
            r for r in media_dict_list
            if (tweet_id := r.get("tweet_id", "")) != "" and (tweet_id not in seen) and (not seen.append(tweet_id))
        ]
        media_dict_list.reverse()
        self.media_db.upsert(media_dict_list)
        logger.info("Media table update -> done")

        # ExternalLink
        logger.info("ExternalLink table update -> start")
        external_link_dict_list = self._interporate_to_external_link(flattened_tweet_list)
        seen = []
        external_link_dict_list = [
            r for r in external_link_dict_list
            if (tweet_id := r.get("tweet_id", "")) != "" and (tweet_id not in seen) and (not seen.append(tweet_id))
        ]
        external_link_dict_list.reverse()
        self.external_link_db.upsert(external_link_dict_list)
        logger.info("ExternalLink table update -> done")

        # Metric
        # logger.info("Metric table update -> start")
        # metric_dict_list = self._interporate_to_metric(flattened_tweet_list, screen_name)
        # self.metric_db.upsert(metric_dict_list)
        # logger.info("Metric table update -> done")

        logger.info("TimelineCrawler likes_crawl -> done")
        return flattened_tweet_list

    def run(self):
        logger.info("TimelineCrawler run -> start")
        authorize_screen_name = self.twitter.authorize_screen_name.name
        logger.info(f"Authorize screen_name is '{authorize_screen_name}'.")
        target_dicts = self.config["target"]  # TODO::authorize複数対応
        for target_dict in target_dicts:
            target_screen_name = target_dict["screen_name"]
            logger.info("----------")
            self.timeline_crawl(target_screen_name)
            logger.info("-----")
            self.likes_crawl(target_screen_name)
            logger.info("----------")
        logger.info("TimelineCrawler run -> done")


if __name__ == "__main__":
    logging.config.fileConfig("./log/logging.ini", disable_existing_loggers=False)
    for name in logging.root.manager.loggerDict:
        if "personaltwilog" in name:
            continue
        if "__main__" in name:
            continue
        getLogger(name).disabled = True

    crawler = TimelineCrawler()
    crawler.run()
    # crawler.timeline_crawl()
    # crawler.likes_crawl()
