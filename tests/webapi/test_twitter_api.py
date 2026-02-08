import sys
import unittest
from collections import namedtuple
from pathlib import Path

import orjson
from mock import MagicMock, call, patch

from personal_twilog.webapi.twitter_api import TwitterAPI
from personal_twilog.webapi.valueobject.screen_name import ScreenName
from personal_twilog.webapi.valueobject.token import Token
from personal_twilog.webapi.valueobject.user_id import UserId
from personal_twilog.webapi.valueobject.user_name import UserName


class TestTwitterAPI(unittest.TestCase):
    def setUp(self):
        self.enterContext(patch("personal_twilog.webapi.twitter_api.logger"))

    def _get_instance(self) -> TwitterAPI:
        mock_twitter = self.enterContext(patch("personal_twilog.webapi.twitter_api.TweeterPy"))
        authorize_screen_name = "authorize_screen_name"
        ct0 = "ct0"
        auth_token = "auth_token"
        instance = TwitterAPI(authorize_screen_name, ct0, auth_token)

        self.assertEqual(
            [call(log_level="WARNING"), call().generate_session(auth_token=auth_token)], mock_twitter.mock_calls
        )
        return instance

    def get_json_dict(self) -> dict:
        return orjson.loads(Path("./tests/cache/users_sample.json").read_bytes())

    def test_init(self):
        instance = self._get_instance()
        authorize_screen_name = ScreenName("authorize_screen_name")
        ct0 = "ct0"
        auth_token = "auth_token"
        self.assertEqual(authorize_screen_name, instance.authorize_screen_name)
        self.assertEqual(ct0, instance.ct0)
        self.assertEqual(auth_token, instance.auth_token)
        self.assertEqual(Token.create(authorize_screen_name, ct0, auth_token), instance.token)

    def test_scraper(self):
        mock_scraper = self.enterContext(patch("personal_twilog.webapi.twitter_api.Scraper"))
        instance = self._get_instance()
        mock_scraper.side_effect = lambda cookies, pbar, debug: "scraper_instance"

        actual = instance.scraper
        self.assertEqual("scraper_instance", actual)
        mock_scraper.assert_called_once_with(
            cookies={"ct0": instance.token.ct0, "auth_token": instance.token.auth_token}, pbar=False, debug=0
        )
        mock_scraper.reset_mock(side_effect=True)

        actual = instance.scraper
        self.assertEqual("scraper_instance", actual)
        mock_scraper.assert_not_called()

    def test_find_values(self):
        instance = self._get_instance()
        json_dict = self.get_json_dict()

        actual = instance._find_values(json_dict, "rest_id")
        self.assertEqual(["12345678"], actual)
        actual = instance._find_values(json_dict, "name")
        self.assertEqual(["dummy_user_name"], actual)
        actual = instance._find_values(json_dict, "screen_name")
        self.assertEqual(["dummy_screen_name"], actual)

        actual = instance._find_values(json_dict, "no_included_key")
        self.assertEqual([], actual)
        actual = instance._find_values("invalid_object", "rest_id")
        self.assertEqual([], actual)

    def test_get_user(self):
        mock_scraper = self.enterContext(patch("personal_twilog.webapi.twitter_api.Scraper"))
        instance = self._get_instance()
        json_dict = self.get_json_dict()
        mock_scraper.return_value.users.side_effect = lambda screen_names: json_dict["data"]["user"]

        screen_name = "dummy_screen_name1"
        actual = instance._get_user(screen_name)
        self.assertEqual(json_dict["data"]["user"], actual)
        self.assertEqual(True, hasattr(instance, "_user_dict"))
        self.assertEqual(json_dict["data"]["user"], instance._user_dict[screen_name])
        mock_scraper.return_value.users.assert_called_once_with([screen_name])
        mock_scraper.return_value.users.reset_mock()

        actual = instance._get_user(screen_name)
        self.assertEqual(json_dict["data"]["user"], actual)
        self.assertEqual(True, hasattr(instance, "_user_dict"))
        self.assertEqual(json_dict["data"]["user"], instance._user_dict[screen_name])
        mock_scraper.return_value.users.assert_not_called()
        mock_scraper.return_value.users.reset_mock()

        screen_name = "dummy_screen_name2"
        actual = instance._get_user(screen_name)
        self.assertEqual(json_dict["data"]["user"], actual)
        self.assertEqual(True, hasattr(instance, "_user_dict"))
        self.assertEqual(json_dict["data"]["user"], instance._user_dict[screen_name])
        mock_scraper.return_value.users.assert_called_once_with([screen_name])
        mock_scraper.return_value.users.reset_mock()

        actual = instance._get_user(ScreenName(screen_name))
        self.assertEqual(json_dict["data"]["user"], actual)
        self.assertEqual(True, hasattr(instance, "_user_dict"))
        self.assertEqual(json_dict["data"]["user"], instance._user_dict[screen_name])
        mock_scraper.return_value.users.assert_not_called()
        mock_scraper.return_value.users.reset_mock()

    def test_get_user_id(self):
        instance = self._get_instance()
        user_id = 12345678
        instance.twitter = MagicMock()
        instance.twitter.me = {"rest_id": user_id}

        screen_name = "dummy_screen_name"
        actual = instance.get_user_id(screen_name)
        expect = UserId(user_id)
        self.assertEqual(expect, actual)

    def test_get_user_name(self):
        instance = self._get_instance()
        screen_name = "dummy_screen_name"
        instance.twitter = MagicMock()
        instance.twitter.me = {"name": screen_name}

        actual = instance.get_user_name(screen_name)
        expect = UserName(screen_name)
        self.assertEqual(expect, actual)

    def test_get_likes(self):
        mock_get_user_id = self.enterContext(patch("personal_twilog.webapi.twitter_api.TwitterAPI.get_user_id"))
        mock_scraper = self.enterContext(patch("personal_twilog.webapi.twitter_api.Scraper"))

        rest_id = 12345678
        Params = namedtuple("Params", ["kind_tweet_results", "min_id", "result"])

        def pre_run(params: Params) -> TwitterAPI:
            instance = self._get_instance()
            mock_get_user_id.reset_mock()
            mock_scraper.reset_mock()

            if params.kind_tweet_results == "normal_tweet":
                mock_scraper.return_value.likes.return_value = {
                    "entries": {"tweet_results": {"result": {"rest_id": str(rest_id)}}}
                }
            elif params.kind_tweet_results == "add_result":
                mock_scraper.return_value.likes.return_value = {
                    "entries": {"tweet_results": {"result": {"tweet": {"rest_id": str(rest_id)}}}}
                }
            elif params.kind_tweet_results == "empty_tweet":
                mock_scraper.return_value.likes.return_value = {"entries": {"tweet_results": {}}}
            elif params.kind_tweet_results == "empty":
                mock_scraper.return_value.likes.return_value = {"entries": []}

            return instance

        def post_run(actual: list[dict], instance: TwitterAPI, params: Params) -> None:
            self.assertEqual(params.result, actual)

        params_list = [
            Params("normal_tweet", -1, [{"result": {"rest_id": str(rest_id)}}]),
            Params("add_result", -1, [{"result": {"rest_id": str(rest_id)}}]),
            Params("empty_tweet", -1, []),
            Params("empty", -1, []),
            Params("normal_tweet", rest_id, [{"result": {"rest_id": str(rest_id)}}]),
        ]
        for params in params_list:
            instance = pre_run(params)
            actual = instance.get_likes("screen_name_1", limit=300, min_id=params.min_id)
            post_run(actual, instance, params)

    def test_get_user_timeline(self):
        mock_get_user_id = self.enterContext(patch("personal_twilog.webapi.twitter_api.TwitterAPI.get_user_id"))
        mock_path = self.enterContext(patch("personal_twilog.webapi.twitter_api.Path"))
        mock_orjson = self.enterContext(patch("personal_twilog.webapi.twitter_api.orjson"))

        rest_id = 12345678
        Params = namedtuple("Params", ["kind_tweet_results", "min_id", "result"])

        def pre_run(params: Params) -> TwitterAPI:
            instance = self._get_instance()
            instance.twitter = MagicMock()
            mock_get_user_id.reset_mock()

            if params.kind_tweet_results == "normal_tweet":
                instance.twitter.get_user_tweets.return_value = {
                    "data": {"tweet_results": {"result": {"rest_id": str(rest_id)}}}
                }
            elif params.kind_tweet_results == "add_result":
                instance.twitter.get_user_tweets.return_value = {
                    "data": {"tweet_results": {"result": {"tweet": {"rest_id": str(rest_id)}}}}
                }
            elif params.kind_tweet_results == "empty_tweet":
                instance.twitter.get_user_tweets.return_value = {"data": {"tweet_results": {}}}
            elif params.kind_tweet_results == "empty":
                instance.twitter.get_user_tweets.return_value = {"data": []}

            return instance

        def post_run(actual: list[dict], instance: TwitterAPI, params: Params) -> None:
            self.assertEqual(params.result, actual)

        params_list = [
            Params("normal_tweet", -1, [{"result": {"rest_id": str(rest_id)}}]),
            Params("add_result", -1, [{"result": {"rest_id": str(rest_id)}}]),
            Params("empty_tweet", -1, []),
            Params("empty", -1, []),
            Params("normal_tweet", rest_id, [{"result": {"rest_id": str(rest_id)}}]),
        ]
        for params in params_list:
            instance = pre_run(params)
            actual = instance.get_user_timeline("screen_name_1", limit=300, min_id=params.min_id)
            post_run(actual, instance, params)


if __name__ == "__main__":
    if sys.argv:
        del sys.argv[1:]
    unittest.main(warnings="ignore")
