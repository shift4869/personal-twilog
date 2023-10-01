# coding: utf-8
import pprint
from logging import INFO, getLogger
from pathlib import Path
from typing import Any

import orjson
from twitter.scraper import Scraper

from personaltwilog.webapi.valueobject.ScreenName import ScreenName
from personaltwilog.webapi.valueobject.Token import Token
from personaltwilog.webapi.valueobject.UserId import UserId
from personaltwilog.webapi.valueobject.UserName import UserName

logger = getLogger(__name__)
logger.setLevel(INFO)


class TwitterAPI():
    authorize_screen_name: ScreenName
    token: Token

    def __init__(self, authorize_screen_name: str, ct0: str, auth_token: str) -> None:
        self.authorize_screen_name = ScreenName(authorize_screen_name)
        self.token = Token.create(self.authorize_screen_name, ct0, auth_token)

    @property
    def scraper(self) -> Scraper:
        if hasattr(self, "_scraper"):
            return self._scraper
        self._scraper = Scraper(
            cookies={"ct0": self.token.ct0, "auth_token": self.token.auth_token}, pbar=False, debug=0
        )
        return self._scraper

    def _find_values(self, obj: Any, key: str) -> list:
        def _inner_helper(inner_obj: Any, inner_key: str, inner_result: list) -> list:
            if isinstance(inner_obj, dict) and (inner_dict := inner_obj):
                for k, v in inner_dict.items():
                    if k == inner_key:
                        inner_result.append(v)
                    inner_result.extend(_inner_helper(v, inner_key, []))
            if isinstance(inner_obj, list) and (inner_list := inner_obj):
                for element in inner_list:
                    inner_result.extend(_inner_helper(element, inner_key, []))
            return inner_result
        return _inner_helper(obj, key, [])

    def _get_user(self, screen_name: ScreenName | str) -> dict:
        if isinstance(screen_name, ScreenName):
            screen_name = screen_name.name

        if hasattr(self, "_user_dict"):
            if result := self._user_dict.get(screen_name, {}):
                return result
        else:
            self._user_dict = {}

        scraper: Scraper = self.scraper
        user_dict: dict = scraper.users([screen_name])
        self._user_dict[screen_name] = user_dict
        return user_dict

    def get_user_id(self, screen_name: ScreenName | str) -> UserId:
        user_dict: dict = self._get_user(screen_name)
        user_id: int = int(self._find_values(user_dict, "rest_id")[0])
        return UserId(user_id)

    def get_user_name(self, screen_name: ScreenName | str) -> UserName:
        user_dict: dict = self._get_user(screen_name)
        user_name: str = self._find_values(user_dict, "name")[0]
        return UserName(user_name)

    def get_likes(self, screen_name: str, limit: int = 300, min_id: int = -1) -> list[dict]:
        logger.info(f"GET like, target user is '{screen_name}' -> start")
        result = []

        target_id = self.get_user_id(screen_name)
        likes = self.scraper.likes([target_id.id], limit=limit)

        # entries のみ対象とする
        entry_list: list[dict] = self._find_values(likes, "entries")
        tweet_results: list[dict] = self._find_values(entry_list, "tweet_results")

        tweet_list = []
        for data_dict in tweet_results:
            # 返信できるアカウントを制限しているときなど階層が異なる場合がある
            if t := data_dict.get("result", {}).get("tweet", {}):
                data_dict: dict = {"result": t}
            if data_dict:
                tweet_list.append(data_dict)
            # min_id が指定されている場合
            if min_id > -1:
                # 現在の id_str を取得して min_id と一致していたら取得を打ち切る
                tweet_ids = []
                try:
                    tweet_ids = self._find_values(data_dict, "rest_id")
                except Exception:
                    continue
                if str(min_id) in tweet_ids:
                    break
        result.extend(tweet_list)

        result = tweet_list[:limit]
        logger.info(f"GET like, target user is '{screen_name}' -> done")
        return result

    def get_user_timeline(self, screen_name: str, limit: int = 300, min_id: int = -1) -> list[dict]:
        logger.info(f"GET user timeline, target user is '{screen_name}' -> start")
        result = []

        target_id = self.get_user_id(screen_name)
        timeline_tweets = self.scraper.tweets_and_replies([target_id.id], limit=limit)

        # entries のみ対象とする（entry にピン留めツイートの情報があるため除外）
        entry_list: list[dict] = self._find_values(timeline_tweets, "entries")
        tweet_results: list[dict] = self._find_values(entry_list, "tweet_results")

        tweet_list = []
        for data_dict in tweet_results:
            # 返信できるアカウントを制限しているときなど階層が異なる場合がある
            if t := data_dict.get("result", {}).get("tweet", {}):
                data_dict: dict = {"result": t}
            if data_dict:
                tweet_list.append(data_dict)
            # min_id が指定されている場合
            if min_id > -1:
                # 現在の id_str を取得して min_id と一致していたら取得を打ち切る
                tweet_ids = []
                try:
                    tweet_ids = self._find_values(data_dict, "rest_id")
                except Exception:
                    continue
                if str(min_id) in tweet_ids:
                    break
        result.extend(tweet_list)

        result = tweet_list[:limit]
        logger.info(f"GET user timeline, target user is '{screen_name}' -> done")
        return result


if __name__ == "__main__":
    import logging.config
    logging.config.fileConfig("./log/logging.ini", disable_existing_loggers=False)

    CONFIG_FILE_NAME = "./config/config.json"
    config_dict = orjson.loads(Path(CONFIG_FILE_NAME).read_bytes())

    config_dict = config_dict["twitter_api_client_list"][0]
    authorize_screen_name = config_dict["authorize"]["screen_name"]
    ct0 = config_dict["authorize"]["ct0"]
    auth_token = config_dict["authorize"]["auth_token"]
    target_screen_name = config_dict["target"][0]["screen_name"]
    twitter = TwitterAPI(authorize_screen_name, ct0, auth_token)

    result: dict | list[dict] = []
    RESPONSE_CACHE_PATH = "./response.txt"

    # pprint.pprint("like 取得")
    # result = twitter.get_likes(target_screen_name, 30, 1633424214756839425)
    # pprint.pprint(len(result))
    # exit(0)

    pprint.pprint("TL 取得")
    # result = twitter.get_user_timeline(target_screen_name, 30, 1686617172276359168)
    result = twitter.get_user_timeline(target_screen_name, 50, -1)
    pprint.pprint(len(result))
