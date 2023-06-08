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

from personaltwilog.webapi.TwitterAPIEndpoint import TwitterAPIEndpoint, TwitterAPIEndpointName
from personaltwilog.webapi.TwitterSession import TwitterSession

logger = getLogger(__name__)
logger.setLevel(INFO)


class TwitterAPI():
    screen_name: str
    target_screen_name: str
    twitter_session: TwitterSession

    def __init__(self, screen_name: str, target_screen_name: str = "") -> None:
        self.screen_name = screen_name
        self.target_screen_name = target_screen_name or screen_name
        self.twitter_session = TwitterSession.create(screen_name)

    @property
    def common_features(self):
        features_dict = {
            "creator_subscriptions_tweet_preview_api_enabled": False,
            "freedom_of_speech_not_reach_fetch_enabled": False,
            "graphql_is_translatable_rweb_tweet_is_translatable_enabled": True,
            "longform_notetweets_consumption_enabled": True,
            "longform_notetweets_inline_media_enabled": True,
            "longform_notetweets_rich_text_read_enabled": True,
            "responsive_web_edit_tweet_api_enabled": True,
            "responsive_web_enhance_cards_enabled": False,
            "responsive_web_graphql_exclude_directive_enabled": True,
            "responsive_web_graphql_skip_user_profile_image_extensions_enabled": False,
            "responsive_web_graphql_timeline_navigation_enabled": True,
            "rweb_lists_timeline_redesign_enabled": False,
            "standardized_nudges_misinfo": True,
            "tweet_awards_web_tipping_enabled": False,
            "tweet_with_visibility_results_prefer_gql_limited_actions_policy_enabled": False,
            "tweetypie_unmention_optimization_enabled": True,
            "verified_phone_label_enabled": False,
            "view_counts_everywhere_api_enabled": True,
        }
        return features_dict

    def _adjust_features(self, estimate_features_dict: dict, expect_features_list: list[str]) -> dict:
        """変動する graphql のパラメータである features の差分を検知して、必要なら修正する

        Notes:
            必要な features が含まれていない場合、デフォルト値 DEFAULT_PARAMS_VALUE で設定する
            不要な features が含まれている場合、除外する

        Args:
            estimate_features_dict (dict): コード記載時に想定した features の辞書
                {
                    "key": bool
                }
            expect_features_list (list[str]): graphql のエンドポイント一覧問い合わせで取得した、
                                              本来送るべき features のkey一覧

        Returns:
            dict: 今回送るべき features の辞書
        """
        DEFAULT_PARAMS_VALUE = False
        result_dict = dict(estimate_features_dict)
        estimate_features_list = list(estimate_features_dict.keys())
        expect_features_list = list(expect_features_list)

        estimate_features_set = set(estimate_features_list)
        expect_features_set = set(expect_features_list)

        diff_necessary = expect_features_set - estimate_features_set
        diff_extra = estimate_features_set - expect_features_set
        if diff_necessary or diff_extra:
            logger.warning(f"features is not expected.")
            if diff_necessary:
                # 必要なパラメータが含まれていない場合、デフォルト値で設定する
                logger.warning(f"features is not include necessary one.")
                for d in diff_necessary:
                    result_dict[d] = DEFAULT_PARAMS_VALUE
                    logger.warning(f'\t"{d}" is set to {DEFAULT_PARAMS_VALUE}.')
            if diff_extra:
                # 不要なパラメータが含まれている場合、削除する
                logger.warning(f"features is include unnecessary one.")
                for d in diff_extra:
                    del result_dict[d]
                    logger.warning(f'\t"{d}" is removed.')
        return result_dict

    def _get_user_id(self, screen_name):
        if not hasattr(self, "_id_name_dict"):
            self._id_name_dict = {}

        user_id = self._id_name_dict.get(screen_name, "")
        if user_id != "":
            return user_id
        user_dict = self.lookup_user_by_screen_name(screen_name)
        user_id = user_dict.get("data", {}) \
                           .get("user", {}) \
                           .get("result", {}) \
                           .get("rest_id", "")
        if user_id == "":
            raise ValueError("Getting user_id is failed.")
        self._id_name_dict[screen_name] = user_id
        return user_id

    def lookup_user_by_screen_name(self, screen_name: str) -> dict:
        logger.info(f"GET user by screen_name, target user is '{screen_name}' -> start")
        url = TwitterAPIEndpoint.make_url(TwitterAPIEndpointName.USER_LOOKUP_BY_USERNAME)
        expect_endpoint_features = TwitterAPIEndpoint.get_features(TwitterAPIEndpointName.USER_LOOKUP_BY_USERNAME)
        features_dict = {
            "creator_subscriptions_tweet_preview_api_enabled": False,
            "hidden_profile_likes_enabled": True,
            "highlights_tweets_tab_ui_enabled": False,
            "responsive_web_graphql_exclude_directive_enabled": True,
            "responsive_web_graphql_skip_user_profile_image_extensions_enabled": False,
            "responsive_web_graphql_timeline_navigation_enabled": True,
            "subscriptions_verification_info_verified_since_enabled": False,
            "verified_phone_label_enabled": False,
        }
        features_dict = self._adjust_features(features_dict, expect_endpoint_features)
        features_str = json.dumps(features_dict, separators=(",", ":"))

        variables_dict = {
            "screen_name": screen_name,
            "withSafetyModeUserFields": True,
        }
        variables_str = json.dumps(variables_dict, separators=(",", ":"))
        params = {
            "variables": variables_str,
            "features": features_str,
        }
        response: Response = self.twitter_session.api_get(
            url,
            params=params
        )
        result: dict = json.loads(response.text)
        logger.info(f"GET user by screen_name, target user is '{screen_name}' -> done")
        return result

    def lookup_me(self) -> dict:
        return self.lookup_user_by_screen_name(self.screen_name)

    def _get_cursor(self, entry: dict) -> str:
        match entry:
            case {
                "entryId": _,
                "sortIndex": _,
                "content": {
                    "entryType": "TimelineTimelineCursor",
                    "__typename": "TimelineTimelineCursor",
                    "value": value,
                    "cursorType": "Bottom"
                }
            }:
                return value
        return ""

    def get_like(self, screen_name: str, limit: int = 300) -> list[dict]:
        logger.info(f"GET like, target user is '{screen_name}' -> start")
        result = []
        url = TwitterAPIEndpoint.make_url(TwitterAPIEndpointName.LIKED_TWEET)
        features_dict = self.common_features
        features_str = json.dumps(features_dict, separators=(",", ":"))

        # user_id 取得
        user_id: str = self._get_user_id(screen_name)

        variables_dict = {
            "count": 20,
            "includePromotedContent": False,
            "userId": user_id,
            "withBirdwatchNotes": False,
            "withClientEventToken": False,
            "withV2Timeline": True,
            "withVoice": True,
        }

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

        # カーソルページング
        cursor = ""
        data_list = []
        tweet_list = []
        while len(tweet_list) <= limit:
            # カーソル設定
            if cursor == "":
                if len(data_list) == 0:
                    # 初回
                    # variables_dict["cursor"] = cursor
                    pass
                else:
                    # エラー
                    break
            else:
                # 2回目以降
                variables_dict["cursor"] = cursor
            variables_str = json.dumps(variables_dict, separators=(",", ":"))

            # リクエスト
            params = {
                "variables": variables_str,
                "features": features_str,
            }
            response: Response = self.twitter_session.api_get(
                url,
                params=params
            )
            data_dict: dict = json.loads(response.text)
            if "error" in data_dict:
                continue
            data_list.append(data_dict)
            logger.info(f"\tuser like {len(data_list):03} pages fetched.")

            # 辞書パースしてカーソルを取得、結果の要素を格納
            prev_tweets_num = len(tweet_list)
            instructions: list[dict] = _get_instructions(data_dict)
            for instruction in instructions:
                entries: list[dict] = instruction.get("entries", [])
                if not entries:
                    continue
                for entry in entries:
                    tweet_results = _get_tweet_results(entry)
                    if tweet_results:
                        tweet_list.append(tweet_results)
                for entry in entries:
                    cursor = self._get_cursor(entry)
                    if cursor != "":
                        break
            now_tweets_num = len(tweet_list)

            if prev_tweets_num == now_tweets_num:
                # 新たに1件もツイートを収集できなかった = 最後まで収集した
                break
            sleep(random.uniform(1.0, 1.5))

        result = tweet_list[:limit]
        logger.info(f"GET like, target user is '{screen_name}' -> done")
        return result

    def get_user_timeline(self, screen_name: str, limit: int = 300, min_id: int = -1) -> list[dict]:
        logger.info(f"GET user timeline, target user is '{screen_name}' -> start")
        result = []
        url = TwitterAPIEndpoint.make_url(TwitterAPIEndpointName.TIMELINE_TWEET)
        expect_endpoint_features = TwitterAPIEndpoint.get_features(TwitterAPIEndpointName.TIMELINE_TWEET)
        features_dict = self.common_features
        features_dict = self._adjust_features(features_dict, expect_endpoint_features)
        features_str = json.dumps(features_dict, separators=(",", ":"))

        # user_id 取得
        user_id: str = self._get_user_id(screen_name)

        variables_dict = {
            "userId": user_id,
            "count": 40,
            "includePromotedContent": False,
            "withQuickPromoteEligibilityTweetFields": False,
            "withVoice": True,
            "withV2Timeline": True
        }

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

        # カーソルページング
        cur_tweet_id = sys.maxsize
        cursor = ""
        data_list = []
        tweet_list = []
        while len(tweet_list) <= limit and (cur_tweet_id > min_id):
            # カーソル設定
            if cursor == "":
                if len(data_list) == 0:
                    # 初回
                    # variables_dict["cursor"] = cursor
                    pass
                else:
                    # エラー
                    break
            else:
                # 2回目以降
                variables_dict["cursor"] = cursor
            variables_str = json.dumps(variables_dict, separators=(",", ":"))

            # リクエスト
            params = {
                "variables": variables_str,
                "features": features_str,
            }
            response: Response = self.twitter_session.api_get(
                url,
                params=params
            )
            data_dict: dict = json.loads(response.text)
            if "error" in data_dict:
                continue
            data_list.append(data_dict)
            logger.info(f"\tuser timeline {len(data_list):03} pages fetched.")

            # 辞書パース
            prev_tweets_num = len(tweet_list)
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
                    # カーソル取得
                    cursor = self._get_cursor(entry)
                    # min_id が指定されている場合
                    if min_id > -1:
                        # 現在の id_str を取得して min_id を下回っていたら取得を打ち切る
                        tweet_id = _get_id_str(tweet_results)
                        if tweet_id > 0 and cur_tweet_id > tweet_id:
                            cur_tweet_id = tweet_id
                        if cur_tweet_id <= min_id:
                            break
            now_tweets_num = len(tweet_list)

            if prev_tweets_num == now_tweets_num:
                # 新たに1件もツイートを収集できなかった = 最後まで収集した
                break
            sleep(random.uniform(1.0, 1.5))

        result = tweet_list[:limit]
        logger.info(f"GET user timeline, target user is '{screen_name}' -> done")
        return result

    def post_tweet(self, tweet_str: str) -> dict:
        logger.info(f"POST tweet -> start")
        url = TwitterAPIEndpoint.make_url(TwitterAPIEndpointName.POST_TWEET)
        features_dict = self.common_features
        variables_dict = {
            "dark_request": False,
            "media": {
                "media_entities": [],
                "possibly_sensitive": False,
            },
            "semantic_annotation_ids": [],
            "tweet_text": tweet_str,
        }
        payload = {
            "features": features_dict,
            "queryId": "1RyAhNwby-gzGCRVsMxKbQ",
            "variables": variables_dict,
        }
        response: Response = self.twitter_session.api_post(
            url,
            payload=payload
        )
        result: dict = json.loads(response.text)
        logger.info(f"POST tweet -> done")
        return result

    def delete_tweet(self, tweet_id: str) -> dict:
        logger.info(f"DELETE tweet -> start")
        url = TwitterAPIEndpoint.make_url(TwitterAPIEndpointName.DELETE_TWEET)
        variables_dict = {
            "dark_request": False,
            "tweet_id": tweet_id,
        }
        payload = {
            "queryId": "VaenaVgh5q5ih7kvyVjgtg",
            "variables": variables_dict,
        }
        response: Response = self.twitter_session.api_post(
            url,
            payload=payload
        )
        result: dict = json.loads(response.text)
        logger.info(f"DELETE tweet -> done")
        return result

    def lookup_tweet(self, tweet_id: str) -> list[dict]:
        logger.info(f"GET tweet detail -> start")
        result = []
        url = TwitterAPIEndpoint.make_url(TwitterAPIEndpointName.TWEETS_LOOKUP)
        features_dict = self.common_features
        features_str = json.dumps(features_dict, separators=(",", ":"))

        variables_dict = {
            "focalTweetId": tweet_id,
            "includePromotedContent": False,
            "with_rux_injections": False,
            "withBirdwatchNotes": True,
            "withCommunity": True,
            "withQuickPromoteEligibilityTweetFields": False,
            "withV2Timeline": True,
            "withVoice": True,
        }
        variables_str = json.dumps(variables_dict, separators=(",", ":"))
        params = {
            "features": features_str,
            "variables": variables_str,
        }
        response: Response = self.twitter_session.api_get(
            url,
            params=params
        )
        result: dict = json.loads(response.text)
        logger.info(f"GET tweet detail -> done")
        return result

    def _get_ff_list(self, screen_name, ff_type: Literal["following", "follower"]) -> list[dict]:
        logger.info(f"GET {ff_type} list -> start")
        result = []
        url = ""
        if ff_type == "following":
            url = TwitterAPIEndpoint.make_url(TwitterAPIEndpointName.FOLLOWING)
        elif ff_type == "follower":
            url = TwitterAPIEndpoint.make_url(TwitterAPIEndpointName.FOLLOWER)
        else:
            return []
        features_dict = self.common_features
        features_str = json.dumps(features_dict, separators=(",", ":"))

        # ユーザーIDを取得する
        user_id: str = self._get_user_id(screen_name)

        variables_dict = {
            "userId": user_id,
            "count": 20,
            "includePromotedContent": False
        }

        def _get_instructions(data_dict: dict) -> list[dict]:
            instructions = data_dict.get("data", {}) \
                                    .get("user", {}) \
                                    .get("result", {}) \
                                    .get("timeline", {}) \
                                    .get("timeline", {}) \
                                    .get("instructions", [{}])
            return instructions

        def _get_user_results(entry: dict) -> dict:
            match entry:
                case {
                    "entryId": _,
                    "sortIndex": _,
                    "content": {
                        "entryType": "TimelineTimelineItem",
                        "__typename": "TimelineTimelineItem",
                        "itemContent": {
                            "user_results": user_results
                        }
                    }
                }:
                    return user_results
            return {}
        # カーソルページング
        cursor = ""
        data_list = []
        ff_list = []
        while not re.findall("^0\|(.*)", cursor):
            # カーソル設定
            if cursor == "":
                if len(data_list) == 0:
                    # 初回
                    # variables_dict["cursor"] = cursor
                    pass
                else:
                    # エラー
                    break
            else:
                # 2回目以降
                variables_dict["cursor"] = cursor
            variables_str = json.dumps(variables_dict, separators=(",", ":"))

            # リクエスト
            params = {
                "variables": variables_str,
                "features": features_str,
            }
            response: Response = self.twitter_session.api_get(
                url,
                params=params
            )
            data_dict: dict = json.loads(response.text)
            if "error" in data_dict:
                continue
            data_list.append(data_dict)
            logger.info(f"\t{ff_type} {len(data_list):03} pages fetched.")

            # 辞書パースしてカーソルを取得
            instructions: list[dict] = _get_instructions(data_dict)
            for instruction in instructions:
                entries: list[dict] = instruction.get("entries", [])
                if not entries:
                    continue
                for entry in entries:
                    user_results = _get_user_results(entry)
                    if user_results:
                        ff_list.append(user_results)
                for entry in entries:
                    cursor = self._get_cursor(entry)
                    if cursor != "":
                        break
            sleep(random.uniform(1.0, 1.5))

        result = ff_list
        # result = tweet_list[:limit]
        logger.info(f"GET {ff_type} list -> done")
        return result

    def get_following_list(self) -> list[dict]:
        return self._get_ff_list("following")

    def get_follower_list(self) -> list[dict]:
        return self._get_ff_list("follower")

    def get_list_member(self, list_id) -> list[dict]:
        logger.info(f"GET list member -> start")
        result = []
        url = TwitterAPIEndpoint.make_url(TwitterAPIEndpointName.GET_MEMBER_FROM_LIST)

        features_dict = self.common_features
        features_str = json.dumps(features_dict, separators=(",", ":"))

        variables_dict = {
            "listId": list_id,
            "count": 20,
            "withSafetyModeUserFields": True
        }

        def _get_instructions(data_dict: dict) -> list[dict]:
            instructions = data_dict.get("data", {}) \
                                    .get("list", {}) \
                                    .get("members_timeline", {}) \
                                    .get("timeline", {}) \
                                    .get("instructions", [{}])
            return instructions

        def _get_user_results(entry: dict) -> dict:
            match entry:
                case {
                    "entryId": _,
                    "sortIndex": _,
                    "content": {
                        "entryType": "TimelineTimelineItem",
                        "__typename": "TimelineTimelineItem",
                        "itemContent": {
                            "user_results": user_results
                        }
                    }
                }:
                    return user_results
            return {}
        # カーソルページング
        cursor = ""
        data_list = []
        user_list = []
        while not re.findall("^0\|(.*)", cursor):
            # カーソル設定
            if cursor == "":
                if len(data_list) == 0:
                    # 初回
                    # variables_dict["cursor"] = cursor
                    pass
                else:
                    # エラー
                    break
            else:
                # 2回目以降
                variables_dict["cursor"] = cursor
            variables_str = json.dumps(variables_dict, separators=(",", ":"))

            # リクエスト
            params = {
                "variables": variables_str,
                "features": features_str,
            }
            response: Response = self.twitter_session.api_get(
                url,
                params=params
            )
            data_dict: dict = json.loads(response.text)
            data_list.append(data_dict)
            logger.info(f"\tlist {len(data_list):03} pages fetched.")

            # 辞書パースしてカーソルを取得
            instructions: list[dict] = _get_instructions(data_dict)
            for instruction in instructions:
                entries: list[dict] = instruction.get("entries", [])
                if not entries:
                    continue
                for entry in entries:
                    user_results = _get_user_results(entry)
                    if user_results:
                        user_list.append(user_results)
                for entry in entries:
                    cursor = self._get_cursor(entry)
                    if cursor != "":
                        break
            sleep(random.uniform(1.0, 1.5))

        result = user_list
        logger.info(f"GET list member -> done")
        return result

    def add_list_member(self, list_id, screen_name: str) -> dict:
        logger.info(f"POST list member, target user is '{screen_name}' -> start")
        url = TwitterAPIEndpoint.make_url(TwitterAPIEndpointName.ADD_MEMBER_TO_LIST)
        features_dict = {
            "blue_business_profile_image_shape_enabled": True,
            "responsive_web_graphql_exclude_directive_enabled": True,
            "responsive_web_graphql_skip_user_profile_image_extensions_enabled": False,
            "responsive_web_graphql_timeline_navigation_enabled": True,
            "verified_phone_label_enabled": False
        }

        # user_id 取得
        user_id: str = self._get_user_id(screen_name)

        variables_dict = {
            "listId": list_id,
            "userId": user_id
        }
        payload = {
            "features": features_dict,
            "variables": variables_dict,
            "queryId": "x0smnIS1jLLXToRYg70g4Q",
        }
        response: Response = self.twitter_session.api_post(
            url,
            payload=payload
        )
        result: dict = json.loads(response.text)
        logger.info(f"POST list member, target user is '{screen_name}' -> done")
        return result

    def get_mute_keyword_list(self) -> dict:
        logger.info("Getting mute word list all -> start")
        url = TwitterAPIEndpoint.make_url(TwitterAPIEndpointName.GET_MUTE_KEYWORD_LIST)
        response: Response = self.twitter_session.api_get(url)
        result: dict = json.loads(response.text)
        logger.info("Getting mute word list all -> done")
        return result

    def mute_keyword(self, keyword: str) -> dict:
        logger.info(f"POST mute word mute, target is '{keyword}' -> start")
        url = TwitterAPIEndpoint.make_url(TwitterAPIEndpointName.POST_MUTE_KEYWORD)
        params = {
            "keyword": keyword,
            "mute_surfaces": "notifications,home_timeline,tweet_replies",
            "mute_option": "",
            "duration": "",
        }
        response: Response = self.twitter_session.api_post(
            url,
            params=params
        )
        result: dict = json.loads(response.text)
        logger.info(f"POST mute word mute, target is '{keyword}' -> done")
        return result

    def unmute_keyword(self, keyword: str) -> dict:
        logger.info(f"POST muted word unmute, target is '{keyword}' -> start")
        url = TwitterAPIEndpoint.make_url(TwitterAPIEndpointName.POST_UNMUTE_KEYWORD)

        r_dict = self.get_mute_keyword_list()
        target_keyword_dict_list: list[dict] = [d for d in r_dict.get("muted_keywords") if d.get("keyword") == keyword]
        if not target_keyword_dict_list:
            raise ValueError("Target muted word is not found.")
        elif len(target_keyword_dict_list) != 1:
            raise ValueError("Target muted word is multiple found.")
        target_keyword_dict = target_keyword_dict_list[0]
        unmute_keyword_id = target_keyword_dict.get("id")

        params = {
            "ids": unmute_keyword_id,
        }
        response: Response = self.twitter_session.api_post(
            url,
            params=params
        )
        result: dict = json.loads(response.text)
        logger.info(f"POST muted word unmute, target is '{keyword}' -> done")
        return result

    def mute_user(self, screen_name: str) -> dict:
        logger.info(f"POST mute user mute, target is '{screen_name}' -> start")
        url = TwitterAPIEndpoint.make_url(TwitterAPIEndpointName.POST_MUTE_USER)
        params = {
            "screen_name": screen_name,
        }
        response: Response = self.twitter_session.api_post(
            url,
            params=params
        )
        result: dict = json.loads(response.text)
        logger.info(f"POST mute user mute, target is '{screen_name}' -> done")
        return result

    def unmute_user(self, screen_name: str) -> dict:
        logger.info(f"POST muted user unmute, target is '{screen_name}' -> start")
        url = TwitterAPIEndpoint.make_url(TwitterAPIEndpointName.POST_UNMUTE_USER)
        params = {
            "screen_name": screen_name,
        }
        response: Response = self.twitter_session.api_post(
            url,
            params=params
        )
        result: dict = json.loads(response.text)
        logger.info(f"POST muted user unmute, target is '{screen_name}' -> done")
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
    target_screen_name = config["twitter"]["target_screen_name"]
    twitter = TwitterAPI(authorize_screen_name, target_screen_name)
    result: dict | list[dict] = []

    def save_response(result_data):
        RESPONSE_CACHE_PATH = "./response.txt"
        with Path(RESPONSE_CACHE_PATH).open("w") as fout:
            json.dump(result_data, fout, indent=4)

    # pprint.pprint("user 情報取得")
    # screen_name = twitter.screen_name
    # result = twitter.lookup_user_by_screen_name(screen_name)
    # save_response(result)
    # pprint.pprint(len(result))

    # pprint.pprint("user me 情報取得")
    # result = twitter.lookup_me()
    # save_response(result)
    # pprint.pprint(len(result))

    # pprint.pprint("like 取得")
    # result = twitter.get_like(twitter.screen_name, 10)
    # save_response(result)
    # pprint.pprint(len(result))

    pprint.pprint("TL 取得")
    result = twitter.get_user_timeline(twitter.target_screen_name, 30)
    save_response(result)
    pprint.pprint(len(result))
    exit(0)

    pprint.pprint("ツイート投稿")
    result = twitter.post_tweet("test")
    save_response(result)
    pprint.pprint(len(result))

    sleep(5)

    pprint.pprint("ツイート詳細取得")
    tweet_id = result.get("data", {}) \
                     .get("create_tweet", {}) \
                     .get("tweet_results", {}) \
                     .get("result", {}) \
                     .get("legacy", {}) \
                     .get("id_str", "")
    result = twitter.lookup_tweet(tweet_id)
    save_response(result)
    pprint.pprint(len(result))

    pprint.pprint("ツイート削除")
    result = twitter.delete_tweet(tweet_id)
    save_response(result)
    pprint.pprint(len(result))

    pprint.pprint("following 取得")
    result = twitter.get_following_list()
    save_response(result)
    pprint.pprint(len(result))
    # for user_dict in result:
    #     legacy = user_dict.get("result", {}).get("legacy", {})
    #     user_id = user_dict.get("result", {}).get("rest_id", "")
    #     user_name = legacy.get("name", "")
    #     screen_name = legacy.get("screen_name", "")
    #     pprint.pprint(f"{user_id}, {user_name}, {screen_name}")

    pprint.pprint("follower 取得")
    result = twitter.get_follower_list()
    save_response(result)
    pprint.pprint(len(result))
    # for user_dict in result:
    #     legacy = user_dict.get("result", {}).get("legacy", {})
    #     user_id = user_dict.get("result", {}).get("rest_id", "")
    #     user_name = legacy.get("name", "")
    #     screen_name = legacy.get("screen_name", "")
    #     pprint.pprint(f"{user_id}, {user_name}, {screen_name}")

    pprint.pprint("list メンバー取得")
    list_id = "1618833354572595200"
    result = twitter.get_list_member(list_id)
    save_response(result)
    pprint.pprint(len(result))

    # pprint.pprint("list メンバー取得")
    # list_id = "1618833354572595200"
    # screen_name = ""
    # result = twitter.add_list_member(list_id, screen_name)
    # save_response(result)
    # pprint.pprint(len(result))

    pprint.pprint("ミュートワードリスト取得")
    result = twitter.get_mute_keyword_list()
    save_response(result)
    pprint.pprint(len(result))

    pprint.pprint("ミュートワード追加")
    keyword = "test"
    result = twitter.mute_keyword(keyword)
    save_response(result)
    pprint.pprint(len(result))

    pprint.pprint("ミュートユーザー追加")
    authorize_screen_name = "o_shift4607"
    result = twitter.mute_user(authorize_screen_name)
    save_response(result)
    pprint.pprint(len(result))

    sleep(5)

    pprint.pprint("ミュートワード解除")
    keyword = "test"
    result = twitter.unmute_keyword(keyword)
    save_response(result)
    pprint.pprint(len(result))

    pprint.pprint("ミュートユーザー解除")
    authorize_screen_name = "o_shift4607"
    result = twitter.unmute_user(authorize_screen_name)
    save_response(result)
    pprint.pprint(len(result))

    pass
