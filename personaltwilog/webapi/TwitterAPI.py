# coding: utf-8
import json
import pprint
import random
import re
import sys
from logging import INFO, getLogger
from pathlib import Path
from time import sleep
from typing import Literal

from requests.models import Response
from twitter.scraper import Scraper

from personaltwilog.webapi.TwitterAPIEndpoint import TwitterAPIEndpoint, TwitterAPIEndpointName
from personaltwilog.webapi.TwitterSession import TwitterSession

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

    def get_likes(self, screen_name: str, limit: int = 300, min_id: int = -1) -> list[dict]:
        logger.info(f"GET like, target user is '{screen_name}' -> start")
        result = []

        def _get_instructions(data_dict: dict) -> list[dict]:
            instructions = data_dict.get("data", {}) \
                                    .get("user", {}) \
                                    .get("result", {}) \
                                    .get("timeline_v2", {}) \
                                    .get("timeline", {}) \
                                    .get("instructions", [{}])
            return instructions

        def _get_tweet_results(entry: dict) -> dict:
            match entry:
                case {
                    "entryId": _,
                    "sortIndex": _,
                    "content": {
                        "entryType": "TimelineTimelineItem",
                        "__typename": "TimelineTimelineItem",
                        "itemContent": {
                            "tweet_results": tweet_results
                        }
                    }
                }:
                    return tweet_results
            return {}

        def _get_id_str(tweet_results: dict) -> int:
            match tweet_results:
                case {
                    "result": {
                        "rest_id": id_str
                    }
                }:
                    return int(id_str)
            return 0

        scraper = Scraper(cookies={"ct0": self.ct0, "auth_token": self.auth_token}, pbar=False)
        likes = scraper.likes([self.target_id], limit=limit)

        cur_tweet_id = sys.maxsize
        tweet_list = []
        for data_dict in likes:
            # 辞書パース
            instructions: list[dict] = _get_instructions(data_dict)
            for instruction in instructions:
                entries: list[dict] = instruction.get("entries", [])
                if not entries:
                    continue
                for entry in entries:
                    # ツイート情報部分取得
                    tweet_results = _get_tweet_results(entry)
                    if tweet_results:
                        tweet_list.append(tweet_results)
                    # min_id が指定されている場合
                    if min_id > -1:
                        # 現在の id_str を取得して min_id と一致していたら取得を打ち切る
                        tweet_id = _get_id_str(tweet_results)
                        if tweet_id > 0:
                            cur_tweet_id = tweet_id
                        if cur_tweet_id == min_id:
                            break

        result = tweet_list[:limit]
        logger.info(f"GET like, target user is '{screen_name}' -> done")
        return result

    def get_user_timeline(self, screen_name: str, limit: int = 300, min_id: int = -1) -> list[dict]:
        logger.info(f"GET user timeline, target user is '{screen_name}' -> start")
        result = []

        def _get_instructions(data_dict: dict) -> list[dict]:
            instructions = data_dict.get("data", {}) \
                                    .get("user", {}) \
                                    .get("result", {}) \
                                    .get("timeline_v2", {}) \
                                    .get("timeline", {}) \
                                    .get("instructions", [{}])
            return instructions

        def _get_tweet_results(entry: dict) -> dict:
            match entry:
                case {
                    "entryId": _,
                    "sortIndex": _,
                    "content": {
                        "entryType": "TimelineTimelineItem",
                        "__typename": "TimelineTimelineItem",
                        "itemContent": {
                            "tweet_results": tweet_results
                        }
                    }
                }:
                    return tweet_results
            return {}

        def _get_id_str(tweet_results: dict) -> int:
            match tweet_results:
                case {
                    "result": {
                        "rest_id": id_str
                    }
                }:
                    return int(id_str)
            return 0

        scraper = Scraper(cookies={"ct0": self.ct0, "auth_token": self.auth_token}, pbar=False)
        timeline_tweets = scraper.tweets_and_replies([self.target_id], limit=limit)

        cur_tweet_id = sys.maxsize
        tweet_list = []
        for data_dict in timeline_tweets:
            # 辞書パース
            instructions: list[dict] = _get_instructions(data_dict)
            for instruction in instructions:
                entries: list[dict] = instruction.get("entries", [])
                if not entries:
                    continue
                for entry in entries:
                    # ツイート情報部分取得
                    tweet_results = _get_tweet_results(entry)
                    if tweet_results:
                        tweet_list.append(tweet_results)
                    # min_id が指定されている場合
                    if min_id > -1:
                        # 現在の id_str を取得して min_id を下回っていたら取得を打ち切る
                        tweet_id = _get_id_str(tweet_results)
                        if tweet_id > 0 and cur_tweet_id > tweet_id:
                            cur_tweet_id = tweet_id
                        if cur_tweet_id <= min_id:
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
            json.dump(result_data, fout, indent=4)

    # pprint.pprint("like 取得")
    # result = twitter.get_likes(twitter.target_screen_name, 10)
    # save_response(result)
    # pprint.pprint(len(result))
    # exit(0)

    pprint.pprint("TL 取得")
    result = twitter.get_user_timeline(twitter.target_screen_name, 30)
    save_response(result)
    pprint.pprint(len(result))
