# coding: utf-8
import json
import pprint
from logging import INFO, getLogger
from pathlib import Path
from typing import Any

from twitter.scraper import Scraper

logger = getLogger(__name__)
logger.setLevel(INFO)


class TwitterAPI():
    screen_name: str
    ct0: str
    auth_token: str
    target_screen_name: str
    target_id: int

    def __init__(self, screen_name: str, ct0: str, auth_token: str, target_screen_name: str, target_id: int) -> None:
        self.screen_name = screen_name
        self.ct0 = ct0
        self.auth_token = auth_token
        self.target_screen_name = target_screen_name or screen_name
        self.target_id = target_id

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

    def get_likes(self, screen_name: str, limit: int = 300, min_id: int = -1) -> list[dict]:
        logger.info(f"GET like, target user is '{screen_name}' -> start")
        result = []

        scraper = Scraper(cookies={"ct0": self.ct0, "auth_token": self.auth_token}, pbar=False)
        likes = scraper.likes([self.target_id], limit=limit)

        # entries のみ対象とする
        entry_list: list[dict] = self._find_values(likes, "entries")[0]
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

        result = tweet_list[:limit]
        logger.info(f"GET like, target user is '{screen_name}' -> done")
        return result

    def get_user_timeline(self, screen_name: str, limit: int = 300, min_id: int = -1) -> list[dict]:
        logger.info(f"GET user timeline, target user is '{screen_name}' -> start")
        result = []

        scraper = Scraper(cookies={"ct0": self.ct0, "auth_token": self.auth_token}, pbar=False)
        timeline_tweets = scraper.tweets_and_replies([self.target_id], limit=limit)

        # entries のみ対象とする（entry にピン留めツイートの情報があるため除外）
        entry_list: list[dict] = self._find_values(timeline_tweets, "entries")[0]
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

        result = tweet_list[:limit]
        logger.info(f"GET user timeline, target user is '{screen_name}' -> done")
        return result


if __name__ == "__main__":
    import logging.config
    logging.config.fileConfig("./log/logging.ini", disable_existing_loggers=False)

    import configparser
    config = configparser.ConfigParser()
    CONFIG_FILE_NAME = "./config/config.ini"
    if not config.read(CONFIG_FILE_NAME, encoding="utf8"):
        raise IOError

    authorize_screen_name = config["twitter"]["authorize_screen_name"]
    ct0 = config["twitter_api_client"]["ct0"]
    auth_token = config["twitter_api_client"]["auth_token"]
    target_screen_name = config["twitter_api_client"]["target_screen_name"]
    target_id = config["twitter_api_client"]["target_id"]
    twitter = TwitterAPI(authorize_screen_name, ct0, auth_token, target_screen_name, target_id)
    result: dict | list[dict] = []

    def save_response(result_data):
        RESPONSE_CACHE_PATH = "./response.txt"
        with Path(RESPONSE_CACHE_PATH).open("w") as fout:
            json.dump(result_data, fout, indent=4, ensure_ascii=False)

    pprint.pprint("like 取得")
    result = twitter.get_likes(twitter.target_screen_name, 30, 1633424214756839425)
    # save_response(result)
    pprint.pprint(len(result))
    exit(0)

    # pprint.pprint("TL 取得")
    # result = twitter.get_user_timeline(twitter.target_screen_name, 30, 1686617172276359168)
    # save_response(result)
    # pprint.pprint(len(result))
