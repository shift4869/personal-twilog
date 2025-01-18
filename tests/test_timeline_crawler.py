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

logger = getLogger("personaltwilog.timeline_crawler")


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
        mock_logger = self.enterContext(patch.object(logger, "info"))
        mock_orjson = self.enterContext(patch("personal_twilog.timeline_crawler.orjson"))
        mock_tweet_db = self.enterContext(patch("personal_twilog.timeline_crawler.TweetDB"))
        mock_likes_db = self.enterContext(patch("personal_twilog.timeline_crawler.LikesDB"))
        mock_media_db = self.enterContext(patch("personal_twilog.timeline_crawler.MediaDB"))
        mock_metric_db = self.enterContext(patch("personal_twilog.timeline_crawler.MetricDB"))
        mock_external_link_db = self.enterContext(patch("personal_twilog.timeline_crawler.ExternalLinkDB"))
        self.enterContext(freezegun.freeze_time("2023-10-07T01:00:00"))

        sample_config_json = self._get_config_json()
        mock_orjson.loads.side_effect = lambda byte_data: sample_config_json
        crawler = TimelineCrawler()

        crawler.TIMELINE_CACHE_FILE_PATH = "./tests/cache/timeline_response.json"
        crawler.LIKES_CACHE_FILE_PATH = "./tests/cache/likes_response.json"

        return crawler

    def test_init(self):
        mock_logger = self.enterContext(patch.object(logger, "info"))
        mock_path = self.enterContext(patch("personal_twilog.timeline_crawler.Path"))
        mock_orjson = self.enterContext(patch("personal_twilog.timeline_crawler.orjson"))
        mock_tweet_db = self.enterContext(patch("personal_twilog.timeline_crawler.TweetDB"))
        mock_likes_db = self.enterContext(patch("personal_twilog.timeline_crawler.LikesDB"))
        mock_media_db = self.enterContext(patch("personal_twilog.timeline_crawler.MediaDB"))
        mock_metric_db = self.enterContext(patch("personal_twilog.timeline_crawler.MetricDB"))
        mock_external_link_db = self.enterContext(patch("personal_twilog.timeline_crawler.ExternalLinkDB"))
        self.enterContext(freezegun.freeze_time("2023-10-07T01:00:00"))

        sample_config_json = self._get_config_json()
        mock_orjson.loads.side_effect = lambda byte_data: sample_config_json

        actual = TimelineCrawler()
        mock_tweet_db.assert_called_once_with()
        mock_likes_db.assert_called_once_with()
        mock_media_db.assert_called_once_with()
        mock_metric_db.assert_called_once_with()
        mock_external_link_db.assert_called_once_with()
        self.assertEqual(sample_config_json["twitter_api_client_list"], actual.config)
        self.assertEqual(mock_tweet_db(), actual.tweet_db)
        self.assertEqual(mock_likes_db(), actual.likes_db)
        self.assertEqual(mock_media_db(), actual.media_db)
        self.assertEqual(mock_metric_db(), actual.metric_db)
        self.assertEqual(mock_external_link_db(), actual.external_link_db)
        self.assertEqual("2023-10-07T01:00:00", actual.registered_at)

    def test_timeline_crawl(self):
        mock_logger = self.enterContext(patch.object(logger, "info"))

        crawler = self._get_instance()
        crawler.twitter = (mock_twitter := MagicMock())
        crawler.tweet_db = (mock_tweet_db := MagicMock())
        crawler.media_db = (mock_media_db := MagicMock())
        crawler.external_link_db = (mock_external_link_db := MagicMock())
        crawler.metric_db = (mock_metric_db := MagicMock())

        screen_name = "target_screen_name"
        tweet_list = ["tweet_list_1", ""]
        metric_parsed_dict = ["metric_parsed_dict"]
        min_id = 100
        mock_tweet_db.select_for_max_id.side_effect = lambda screen_name: min_id

        mock_path = self.enterContext(patch("personal_twilog.timeline_crawler.Path"))
        mock_tweet_parser = self.enterContext(patch("personal_twilog.timeline_crawler.TweetParser"))
        mock_media_parser = self.enterContext(patch("personal_twilog.timeline_crawler.MediaParser"))
        mock_external_link_parser = self.enterContext(patch("personal_twilog.timeline_crawler.ExternalLinkParser"))
        mock_metric_parser = self.enterContext(patch("personal_twilog.timeline_crawler.MetricParser"))
        mock_timeline_stats = self.enterContext(patch("personal_twilog.timeline_crawler.TimelineStats"))
        mock_orjson = self.enterContext(patch("personal_twilog.timeline_crawler.orjson"))

        Params = namedtuple("Params", ["is_twitter", "tweet_list", "metric_parsed_dict", "result"])

        def pre_run(params: Params):
            mock_twitter.reset_mock()
            mock_orjson.reset_mock()
            if params.is_twitter:
                mock_twitter.get_user_timeline.side_effect = lambda screen_name, limit, min_id: params.tweet_list
                crawler.twitter = mock_twitter
            else:
                crawler.twitter = None
                mock_orjson.loads.side_effect = lambda _: params.tweet_list[:-1]

            mock_tweet_db.reset_mock()
            mock_media_db.reset_mock()
            mock_external_link_db.reset_mock()
            mock_metric_db.reset_mock()

            mock_tweet_parser.reset_mock()
            mock_media_parser.reset_mock()
            mock_external_link_parser.reset_mock()

            mock_metric_parser.reset_mock()
            metric_mock = MagicMock()
            metric_mock.parse.return_value = params.metric_parsed_dict
            mock_metric_parser.side_effect = lambda t, registered_at, screen_name: metric_mock
            mock_timeline_stats.reset_mock()

        def post_run(params: Params, actual):
            self.assertEqual(params.result, actual)
            limit = 300
            tweet_list = params.tweet_list[:-1]
            if params.is_twitter:
                self.assertEqual(
                    [call.__bool__(), call.get_user_timeline(screen_name, limit, min_id)],
                    mock_twitter.mock_calls,
                )
                if tweet_list:
                    mock_orjson.dumps.assert_called()
                else:
                    mock_orjson.dumps.assert_not_called()
            else:
                mock_twitter.assert_not_called()
                mock_orjson.loads.assert_called()

            if not tweet_list:
                mock_tweet_db.assert_not_called()
                mock_media_db.assert_not_called()
                mock_external_link_db.assert_not_called()
                mock_metric_db.assert_not_called()

                mock_tweet_parser.assert_not_called()
                mock_media_parser.assert_not_called()
                mock_external_link_parser.assert_not_called()
                mock_metric_parser.assert_not_called()
                mock_timeline_stats.assert_not_called()
                return

            self.assertEqual(
                [call(tweet_list, crawler.registered_at), call().parse()],
                mock_tweet_parser.mock_calls,
            )
            self.assertEqual(
                [call.select_for_max_id(screen_name), call.upsert(mock_tweet_parser().parse())],
                mock_tweet_db.mock_calls,
            )

            self.assertEqual(
                [call(tweet_list, crawler.registered_at), call().parse()],
                mock_media_parser.mock_calls,
            )
            self.assertEqual(
                [call.upsert(mock_media_parser().parse())],
                mock_media_db.mock_calls,
            )

            self.assertEqual(
                [call(tweet_list, crawler.registered_at), call().parse()],
                mock_external_link_parser.mock_calls,
            )
            self.assertEqual(
                [call.upsert(mock_external_link_parser().parse())],
                mock_external_link_db.mock_calls,
            )

            self.assertEqual(
                [call(tweet_list, crawler.registered_at, screen_name)],
                mock_metric_parser.mock_calls,
            )
            if params.metric_parsed_dict:
                metric_parsed_dict = params.metric_parsed_dict
                self.assertEqual(
                    [call(metric_parsed_dict[0], mock_tweet_db), call().to_dict()],
                    mock_timeline_stats.mock_calls,
                )
                self.assertEqual(
                    [call.upsert([mock_timeline_stats().to_dict()])],
                    mock_metric_db.mock_calls,
                )
            else:
                mock_timeline_stats.assert_not_called()
                mock_metric_db.assert_not_called()

        params_list = [
            Params(True, tweet_list, metric_parsed_dict, CrawlResultStatus.DONE),
            Params(True, tweet_list, [], CrawlResultStatus.DONE),
            Params(True, [], [], CrawlResultStatus.NO_UPDATE),
            Params(False, tweet_list, metric_parsed_dict, CrawlResultStatus.DONE),
            Params(False, tweet_list, [], CrawlResultStatus.DONE),
            Params(False, [], [], CrawlResultStatus.NO_UPDATE),
        ]
        for params in params_list:
            pre_run(params)
            actual = crawler.timeline_crawl(screen_name)
            post_run(params, actual)

    def test_likes_crawl(self):
        mock_logger = self.enterContext(patch.object(logger, "info"))

        crawler = self._get_instance()
        crawler.twitter = (mock_twitter := MagicMock())
        crawler.likes_db = (mock_likes_db := MagicMock())
        crawler.media_db = (mock_media_db := MagicMock())
        crawler.external_link_db = (mock_external_link_db := MagicMock())
        crawler.metric_db = (mock_metric_db := MagicMock())

        screen_name = "target_screen_name"
        user_id = 11111
        user_name = "target_user_name"
        tweet_list = ["tweet_list_1", ""]
        min_id = 100
        mock_likes_db.select_for_max_id.side_effect = lambda screen_name: min_id

        mock_path = self.enterContext(patch("personal_twilog.timeline_crawler.Path"))
        mock_likes_parser = self.enterContext(patch("personal_twilog.timeline_crawler.LikesParser"))
        mock_media_parser = self.enterContext(patch("personal_twilog.timeline_crawler.MediaParser"))
        mock_external_link_parser = self.enterContext(patch("personal_twilog.timeline_crawler.ExternalLinkParser"))
        mock_orjson = self.enterContext(patch("personal_twilog.timeline_crawler.orjson"))

        Params = namedtuple("Params", ["is_twitter", "tweet_list", "result"])

        def pre_run(params: Params):
            mock_twitter.reset_mock()
            mock_orjson.reset_mock()
            if params.is_twitter:
                mock_twitter.get_likes.side_effect = lambda screen_name, limit, min_id: params.tweet_list
                mock_twitter.get_user_id.side_effect = lambda screen_name: UserId(user_id)
                mock_twitter.get_user_name.side_effect = lambda screen_name: UserName(user_name)
                crawler.twitter = mock_twitter
            else:
                crawler.twitter = None
                mock_orjson.loads.side_effect = lambda _: params.tweet_list[:-1]

            mock_likes_db.reset_mock()
            mock_media_db.reset_mock()
            mock_external_link_db.reset_mock()
            mock_metric_db.reset_mock()

            mock_likes_parser.reset_mock()
            mock_media_parser.reset_mock()
            mock_external_link_parser.reset_mock()

        def post_run(params: Params, actual):
            self.assertEqual(params.result, actual)
            limit = 300
            tweet_list = params.tweet_list[:-1]
            if params.is_twitter:
                if tweet_list:
                    self.assertEqual(
                        [
                            call.__bool__(),
                            call.get_likes(screen_name, limit, min_id),
                            call.__bool__(),
                            call.get_user_id(screen_name),
                            call.__bool__(),
                            call.get_user_name(screen_name),
                        ],
                        mock_twitter.mock_calls,
                    )
                    mock_orjson.dumps.assert_called()
                else:
                    self.assertEqual(
                        [
                            call.__bool__(),
                            call.get_likes(screen_name, limit, min_id),
                        ],
                        mock_twitter.mock_calls,
                    )
                    mock_orjson.dumps.assert_not_called()
            else:
                mock_twitter.assert_not_called()
                mock_orjson.loads.assert_called()

            if not tweet_list:
                mock_likes_db.assert_not_called()
                mock_media_db.assert_not_called()
                mock_external_link_db.assert_not_called()
                mock_metric_db.assert_not_called()

                mock_likes_parser.assert_not_called()
                mock_media_parser.assert_not_called()
                mock_external_link_parser.assert_not_called()
                return

            if params.is_twitter:
                self.assertEqual(
                    [call(tweet_list, crawler.registered_at, str(user_id), user_name, screen_name), call().parse()],
                    mock_likes_parser.mock_calls,
                )
            else:
                self.assertEqual(
                    [call(tweet_list, crawler.registered_at, "", "", screen_name), call().parse()],
                    mock_likes_parser.mock_calls,
                )
            self.assertEqual(
                [call.select_for_max_id(screen_name), call.upsert(mock_likes_parser().parse())],
                mock_likes_db.mock_calls,
            )

            self.assertEqual(
                [call(tweet_list, crawler.registered_at), call().parse()],
                mock_media_parser.mock_calls,
            )
            self.assertEqual(
                [call.upsert(mock_media_parser().parse())],
                mock_media_db.mock_calls,
            )

            self.assertEqual(
                [call(tweet_list, crawler.registered_at), call().parse()],
                mock_external_link_parser.mock_calls,
            )
            self.assertEqual(
                [call.upsert(mock_external_link_parser().parse())],
                mock_external_link_db.mock_calls,
            )

            mock_metric_db.assert_not_called()

        params_list = [
            Params(True, tweet_list, CrawlResultStatus.DONE),
            Params(True, [], CrawlResultStatus.NO_UPDATE),
            Params(False, tweet_list, CrawlResultStatus.DONE),
            Params(False, [], CrawlResultStatus.NO_UPDATE),
        ]
        for params in params_list:
            pre_run(params)
            actual = crawler.likes_crawl(screen_name)
            post_run(params, actual)

    def test_clean_cache(self):
        mock_logger = self.enterContext(patch.object(logger, "info"))
        self.enterContext(freezegun.freeze_time("2025-01-18T01:00:00"))

        crawler = self._get_instance()
        base_path: Path = Path("./tests/data")

        Params = namedtuple("Params", ["file_num", "dir_num", "file_num_in_dir", "is_cutoff", "cutoff_days"])

        def pre_run(params: Params):
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

        def post_run(params: Params, actual):
            self.assertIsNone(actual)
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
            pre_run(params)
            actual = crawler.clean_cache(base_path, params.cutoff_days)
            post_run(params, actual)

    def test_run(self):
        mock_logger = self.enterContext(patch.object(logger, "info"))
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
