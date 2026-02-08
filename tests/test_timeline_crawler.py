import os
import shutil
import sys
import unittest
from collections import namedtuple
from datetime import datetime
from logging import getLogger
from pathlib import Path

import freezegun
from dateutil.relativedelta import relativedelta
from mock import MagicMock, call, patch

from personal_twilog.timeline_crawler import CrawlResultStatus, TimelineCrawler
from personal_twilog.webapi.valueobject.user_id import UserId
from personal_twilog.webapi.valueobject.user_name import UserName


class TestTimelineCrawler(unittest.TestCase):
    def _make_user_dict(self, index: int, is_enable: bool) -> dict:
        screen_name = f"screen_name_{index}"
        ct0 = f"ct0_{index}"
        auth_token = f"auth_token_{index}"
        enable = "enable" if is_enable else "disable"
        return {"status": enable, "screen_name": screen_name, "ct0": ct0, "auth_token": auth_token}

    def _get_config_json(self, enable_num: int = 1, disable_num: int = 0) -> dict:
        enable_user_list = [self._make_user_dict(i, True) for i in range(enable_num)]
        disable_user_list = [self._make_user_dict(i, False) for i in range(disable_num)]
        user_list = enable_user_list + disable_user_list
        return {"twitter_api_client_list": user_list}

    def _get_instance(self) -> TimelineCrawler:
        self.mock_logger = self.enterContext(patch("personal_twilog.timeline_crawler.logger"))
        self.mock_orjson = self.enterContext(patch("personal_twilog.timeline_crawler.orjson"))
        self.mock_tweet_db = self.enterContext(patch("personal_twilog.timeline_crawler.TweetDB"))
        self.mock_likes_db = self.enterContext(patch("personal_twilog.timeline_crawler.LikesDB"))
        self.mock_media_db = self.enterContext(patch("personal_twilog.timeline_crawler.MediaDB"))
        self.mock_metric_db = self.enterContext(patch("personal_twilog.timeline_crawler.MetricDB"))
        self.mock_external_link_db = self.enterContext(patch("personal_twilog.timeline_crawler.ExternalLinkDB"))
        self.enterContext(freezegun.freeze_time("2026-02-08T01:00:00"))

        sample_config_json = self._get_config_json()
        self.mock_orjson.loads.side_effect = lambda byte_data: sample_config_json
        crawler = TimelineCrawler()

        crawler.TIMELINE_CACHE_FILE_PATH = "./tests/cache/timeline_response.json"
        crawler.LIKES_CACHE_FILE_PATH = "./tests/cache/likes_response.json"

        return crawler

    def test_init(self):
        instance = self._get_instance()

        self.mock_tweet_db.assert_called_once_with()
        self.mock_likes_db.assert_called_once_with()
        self.mock_media_db.assert_called_once_with()
        self.mock_metric_db.assert_called_once_with()
        self.mock_external_link_db.assert_called_once_with()
        sample_config_json = self._get_config_json()
        self.assertEqual(sample_config_json["twitter_api_client_list"], instance.config)
        self.assertEqual(self.mock_tweet_db(), instance.tweet_db)
        self.assertEqual(self.mock_likes_db(), instance.likes_db)
        self.assertEqual(self.mock_media_db(), instance.media_db)
        self.assertEqual(self.mock_metric_db(), instance.metric_db)
        self.assertEqual(self.mock_external_link_db(), instance.external_link_db)
        self.assertEqual("2026-02-08T01:00:00", instance.registered_at)

    def test_timeline_crawl(self):
        mock_path = self.enterContext(patch("personal_twilog.timeline_crawler.Path"))
        # mock_orjson = self.enterContext(patch("personal_twilog.timeline_crawler.orjson"))
        mock_tweet_parser = self.enterContext(patch("personal_twilog.timeline_crawler.TweetParser"))
        mock_memo_writer = self.enterContext(patch("personal_twilog.timeline_crawler.MemoWriter"))
        mock_media_parser = self.enterContext(patch("personal_twilog.timeline_crawler.MediaParser"))
        mock_external_link_parser = self.enterContext(patch("personal_twilog.timeline_crawler.ExternalLinkParser"))
        mock_metric_parser = self.enterContext(patch("personal_twilog.timeline_crawler.MetricParser"))
        mock_timeline_stats = self.enterContext(patch("personal_twilog.timeline_crawler.TimelineStats"))

        Params = namedtuple("Params", ["is_twitter", "kind_tweet_list", "kind_metric_parsed_dict", "result"])

        def pre_run(params: Params) -> TimelineCrawler:
            instance = self._get_instance()
            instance.tweet_db = MagicMock()
            instance.likes_db = MagicMock()
            instance.media_db = MagicMock()
            instance.metric_db = MagicMock()
            instance.external_link_db = MagicMock()

            min_id = 100
            instance.tweet_db.select_for_max_id.return_value = min_id

            self.mock_orjson.reset_mock()
            instance.twitter = MagicMock()
            # mock_orjson.reset_mock()
            mock_path.reset_mock()
            mock_tweet_parser.reset_mock()
            mock_memo_writer.reset_mock()
            mock_media_parser.reset_mock()
            mock_external_link_parser.reset_mock()
            mock_metric_parser.reset_mock()
            mock_timeline_stats.reset_mock()

            if params.is_twitter:
                if params.kind_tweet_list == "valid":
                    tweet_list = ["tweet_list_1", ""]
                    instance.twitter.get_user_timeline.return_value = tweet_list
                else:  # "empty"
                    instance.twitter.get_user_timeline.return_value = []
            else:
                instance.twitter = None
                if params.kind_tweet_list == "valid":
                    tweet_list = ["tweet_list_1", ""]
                    self.mock_orjson.loads.side_effect = lambda byte_data: tweet_list
                else:  # "empty"
                    self.mock_orjson.loads.side_effect = lambda byte_data: []

            if params.kind_metric_parsed_dict == "valid":
                metric_parsed_dict = ["metric_parsed_dict"]
                mock_metric_parser.return_value.parse.return_value = metric_parsed_dict
            else:  # "empty"
                mock_metric_parser.return_value.parse.return_value = []
            return instance

        def post_run(actual: CrawlResultStatus, instance: TimelineCrawler, params: Params) -> None:
            self.assertEqual(params.result, actual)

            if params.is_twitter:
                instance.twitter.get_user_timeline.assert_called_once_with("screen_name_1", 300, 100)
                if params.kind_tweet_list == "valid":
                    mock_path.assert_called()
                else:  # "empty"
                    mock_path.assert_not_called()
            else:
                mock_path.assert_called()

            if params.kind_tweet_list != "valid":
                mock_tweet_parser.assert_not_called()
                mock_memo_writer.assert_not_called()
                mock_media_parser.assert_not_called()
                mock_external_link_parser.assert_not_called()
                mock_metric_parser.assert_not_called()
                mock_timeline_stats.assert_not_called()
                return

            mock_tweet_parser.assert_called()
            instance.tweet_db.upsert.assert_called()
            mock_memo_writer.assert_called()
            mock_media_parser.assert_called()
            instance.media_db.upsert.assert_called()
            mock_external_link_parser.assert_called()
            instance.external_link_db.upsert.assert_called()

            if params.kind_metric_parsed_dict != "valid":
                mock_timeline_stats.assert_not_called()
                instance.metric_db.upsert.assert_not_called()
            else:  # "empty"
                mock_timeline_stats.assert_called()
                instance.metric_db.upsert.assert_called()

        params_list = [
            Params(True, "valid", "valid", CrawlResultStatus.DONE),
            Params(True, "valid", "empty", CrawlResultStatus.DONE),
            Params(False, "valid", "valid", CrawlResultStatus.DONE),
            Params(True, "empty", "valid", CrawlResultStatus.NO_UPDATE),
            Params(False, "empty", "valid", CrawlResultStatus.NO_UPDATE),
        ]
        for params in params_list:
            instance = pre_run(params)
            actual = instance.timeline_crawl("screen_name_1")
            post_run(actual, instance, params)

    def test_likes_crawl(self):
        mock_path = self.enterContext(patch("personal_twilog.timeline_crawler.Path"))
        mock_likes_parser = self.enterContext(patch("personal_twilog.timeline_crawler.LikesParser"))
        mock_media_parser = self.enterContext(patch("personal_twilog.timeline_crawler.MediaParser"))
        mock_external_link_parser = self.enterContext(patch("personal_twilog.timeline_crawler.ExternalLinkParser"))

        Params = namedtuple("Params", ["is_twitter", "kind_tweet_list", "result"])

        def pre_run(params: Params) -> TimelineCrawler:
            instance = self._get_instance()
            instance.likes_db = MagicMock()
            instance.media_db = MagicMock()
            instance.metric_db = MagicMock()
            instance.external_link_db = MagicMock()

            min_id = 100
            instance.likes_db.select_for_max_id.return_value = min_id

            self.mock_orjson.reset_mock()
            instance.twitter = MagicMock()
            # mock_orjson.reset_mock()
            mock_path.reset_mock()
            mock_likes_parser.reset_mock()
            mock_media_parser.reset_mock()
            mock_external_link_parser.reset_mock()

            if params.is_twitter:
                if params.kind_tweet_list == "valid":
                    tweet_list = ["tweet_list_1", ""]
                    instance.twitter.get_likes.return_value = tweet_list
                else:  # "empty"
                    instance.twitter.get_likes.return_value = []
            else:
                instance.twitter = None
                if params.kind_tweet_list == "valid":
                    tweet_list = ["tweet_list_1", ""]
                    self.mock_orjson.loads.side_effect = lambda byte_data: tweet_list
                else:  # "empty"
                    self.mock_orjson.loads.side_effect = lambda byte_data: []
            return instance

        def post_run(actual: CrawlResultStatus, instance: TimelineCrawler, params: Params) -> None:
            self.assertEqual(params.result, actual)

            if params.is_twitter:
                instance.twitter.get_likes.assert_called_once_with("screen_name_1", 300, 100)
                if params.kind_tweet_list == "valid":
                    mock_path.assert_called()
                else:  # "empty"
                    mock_path.assert_not_called()
            else:
                mock_path.assert_called()

            if params.kind_tweet_list != "valid":
                mock_likes_parser.assert_not_called()
                mock_media_parser.assert_not_called()
                mock_external_link_parser.assert_not_called()
                return

            mock_likes_parser.assert_called()
            instance.likes_db.upsert.assert_called()
            mock_media_parser.assert_called()
            instance.media_db.upsert.assert_called()
            mock_external_link_parser.assert_called()
            instance.external_link_db.upsert.assert_called()

        params_list = [
            Params(True, "valid", CrawlResultStatus.DONE),
            Params(False, "valid", CrawlResultStatus.DONE),
            Params(True, "empty", CrawlResultStatus.NO_UPDATE),
            Params(False, "empty", CrawlResultStatus.NO_UPDATE),
        ]
        for params in params_list:
            instance = pre_run(params)
            actual = instance.likes_crawl("screen_name_1")
            post_run(actual, instance, params)

    def test_clean_cache(self):
        base_path: Path = Path("./tests/data")
        Params = namedtuple("Params", ["file_num", "dir_num", "file_num_in_dir", "is_cutoff", "cutoff_days"])

        def pre_run(params: Params) -> TimelineCrawler:
            instance = self._get_instance()

            base_path.mkdir(exist_ok=True, parents=True)
            dir_list: list[Path] = []
            for i in range(params.file_num):
                file_path = base_path / f"dummy_file{i}.zip"
                file_path.touch()
                if params.is_cutoff:
                    now_date = datetime.now()
                    cutoff_date = now_date - relativedelta(days=params.cutoff_days + 1)
                    utime = cutoff_date.timestamp()
                    os.utime(file_path, (utime, utime))
            for i in range(params.dir_num):
                dir_path = base_path / f"dir_num{i}"
                dir_path.mkdir(exist_ok=True, parents=True)
                dir_list.append(dir_path)
            for dir_path in dir_list:
                if params.file_num_in_dir > 0:
                    for i in range(params.file_num_in_dir):
                        (dir_path / f"dummy_file_in_dir{i}.json").touch()
                else:
                    (dir_path / f"dummy_dir").mkdir()

            return instance

        def post_run(params: Params, instance: TimelineCrawler):
            dir_list = [folder_path for folder_path in base_path.iterdir() if folder_path.is_dir()]
            self.assertEqual([], dir_list)

            for i in range(params.file_num):
                file_path = base_path / f"dummy_file{i}.zip"
                if not params.is_cutoff:
                    self.assertTrue(file_path.is_file())
                else:
                    self.assertFalse(file_path.exists())

            now_date = datetime.now()
            now_date_str = now_date.strftime("%Y%m%d")
            zipfile_path = base_path / f"cache_{now_date_str}.zip"
            self.assertTrue(zipfile_path.is_file())
            shutil.rmtree(base_path)

        params_list = [
            Params(1, 4, 5, False, 7),
            Params(7, 4, 5, False, 7),
            Params(1, 4, 5, True, 7),
            Params(7, 4, 5, True, 7),
            Params(1, 4, 0, True, 7),
        ]
        for params in params_list:
            instance = pre_run(params)
            actual = instance.clean_cache(base_path, params.cutoff_days)
            self.assertIsNone(actual)
            post_run(params, instance)

    def test_run(self):
        mock_debug = self.enterContext(patch("personal_twilog.timeline_crawler.DEBUG"))
        mock_twitter_api = self.enterContext(patch("personal_twilog.timeline_crawler.TwitterAPI"))
        mock_timeline_crawl = self.enterContext(
            patch("personal_twilog.timeline_crawler.TimelineCrawler.timeline_crawl")
        )
        mock_likes_crawl = self.enterContext(patch("personal_twilog.timeline_crawler.TimelineCrawler.likes_crawl"))
        mock_clean_cache = self.enterContext(patch("personal_twilog.timeline_crawler.TimelineCrawler.clean_cache"))
        crawler = self._get_instance()

        Params = namedtuple("Params", ["is_debug", "enable_num", "disable_num"])

        def pre_run(params: Params):
            mock_debug.reset_mock()
            mock_debug.__bool__.return_value = params.is_debug

            mock_twitter_api.reset_mock()
            mock_timeline_crawl.reset_mock()
            mock_likes_crawl.reset_mock()
            mock_clean_cache.reset_mock()

            config = self._get_config_json(params.enable_num, params.disable_num)
            crawler.config = config["twitter_api_client_list"]

        def post_run(params: Params, actual):
            self.assertIsNone(actual)
            twitter_api_calls = []
            timeline_crawl_calls = []
            likes_crawl_calls = []
            target_dicts = crawler.config
            for target_dict in target_dicts:
                is_enable = "enable" == target_dict["status"]
                screen_name = target_dict["screen_name"]
                if not is_enable:
                    continue
                ct0 = target_dict["ct0"]
                auth_token = target_dict["auth_token"]
                if not params.is_debug:
                    twitter_api_calls.append(call(screen_name, ct0, auth_token))
                timeline_crawl_calls.append(call(screen_name))
                likes_crawl_calls.append(call(screen_name))

            self.assertEqual(twitter_api_calls, mock_twitter_api.mock_calls)
            self.assertEqual(timeline_crawl_calls, mock_timeline_crawl.mock_calls)
            self.assertEqual(likes_crawl_calls, mock_likes_crawl.mock_calls)
            mock_clean_cache.assert_called_once()

        params_list = [
            Params(False, 1, 0),
            Params(False, 0, 1),
            Params(False, 1, 1),
            Params(False, 2, 2),
            Params(False, 0, 0),
            Params(True, 1, 0),
            Params(True, 0, 1),
            Params(True, 1, 1),
            Params(True, 2, 2),
        ]
        for params in params_list:
            pre_run(params)
            actual = crawler.run()
            post_run(params, actual)


if __name__ == "__main__":
    if sys.argv:
        del sys.argv[1:]
    unittest.main(warnings="ignore")
