import re
import sys
import urllib.parse
from abc import abstractmethod
from datetime import datetime, timedelta
from pathlib import Path

import requests

from personaltwilog.Util import find_values


class ParserBase:
    tweet_dict_list: list[dict]
    registered_at: str

    def __init__(self, tweet_dict_list: list[dict], registered_at: str) -> None:
        if not isinstance(tweet_dict_list, list):
            raise TypeError("Argument tweet_dict_list is not list.")
        if not all([isinstance(d, dict) for d in tweet_dict_list]):
            raise TypeError("Argument tweet_dict_list is not list[dict].")
        if not isinstance(registered_at, str):
            raise TypeError("Argument registered_at is not str.")

        self.tweet_dict_list = tweet_dict_list
        self.registered_at = registered_at

    @property
    def result(self) -> list[dict]:
        return self.tweet_dict_list

    def _remove_duplicates(self, dict_list: list[dict]) -> list[dict]:
        if not isinstance(dict_list, list):
            raise TypeError("Argument dict_list is not list.")
        if not all([isinstance(d, dict) for d in dict_list]):
            raise TypeError("Argument dict_list is not list[dict].")

        dup_target_key = "tweet_id"
        key_check = [d.get(dup_target_key, "") != "" for d in dict_list]
        if not all(key_check):
            raise ValueError(f"Argument dict_list include element that not has '{dup_target_key}' key.")

        seen = []
        dict_list = [
            d for d in dict_list
            if (tweet_id := d.get(dup_target_key, "")) != "" and (tweet_id not in seen) and (not seen.append(tweet_id))
        ]
        return dict_list

    def _get_external_link_type(self, external_link_url: str) -> str:
        if not isinstance(external_link_url, str):
            raise TypeError("Argument external_link_url is not str.")

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
        if not isinstance(entities, dict):
            raise TypeError("Argument entities is not dict.")
        # match entities:
        #     case {"urls": urls_dict}:
        #         expanded_urls = []
        #         for url_dict in urls_dict:
        #             expanded_url = url_dict.get("expanded_url", "")
        #             if not expanded_url:
        #                 continue
        #             expanded_urls.append(expanded_url)
        #         return {"expanded_urls": expanded_urls}
        # return {}
        expanded_urls = find_values(entities, "expanded_url")
        return {"expanded_urls": expanded_urls} if expanded_urls else {}

    def _match_media(self, media: dict) -> dict:
        """mediaから保存対象のメディアURLを取得する

        Args:
            media_dict (dict): tweet.legacy.extended_entities.media[] の要素

        Returns:
            result (dict): 成功時 result, そうでなければ空辞書
        """
        if not isinstance(media, dict):
            raise TypeError("Argument media is not dict.")
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
        file_size = -1
        try:
            # HEADリクエストを送信してレスポンスヘッダーを取得
            response = requests.head(media_url)
            response.raise_for_status()
            # Content-Lengthフィールドからファイルサイズを取得
            file_size = int(response.headers.get("Content-Length", 0))
        except Exception as e:
            file_size = -1
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
            # 辞書構造が異なる場合がある
            if tweet.get("__typename", "") == "TweetWithVisibilityResults":
                # 閲覧アカウントを制限しているツイート
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

    @abstractmethod
    def parse(self):
        pass


if __name__ == "__main__":
    pass
