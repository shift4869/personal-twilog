import sys
import unittest
from contextlib import ExitStack
from logging import getLogger
from pathlib import Path

import freezegun
import orjson
from mock import MagicMock, call, patch

from personaltwilog.TimelineCrawler import CrawlResultStatus, TimelineCrawler

logger = getLogger("personaltwilog.TimelineCrawler")


class TestTimelineCrawler(unittest.TestCase):
    def get_config_json(self) -> dict:
        authorize_screen_name = "screen_name_1"
        ct0 = "ct0_1"
        auth_token = "auth_token_1"
        return {
            "twitter_api_client_list": [
                {
                    "authorize": {
                        "screen_name": authorize_screen_name,
                        "ct0": ct0,
                        "auth_token": auth_token
                    },
                    "target": [
                        {
                            "screen_name": "target_screen_name",
                            "status": "enable"
                        }
                    ]
                }
            ]
        }

    def get_instance(self) -> TimelineCrawler:
        with ExitStack() as stack:
            mock_logger = stack.enter_context(patch.object(logger, "info"))
            mock_path = stack.enter_context(patch("personaltwilog.TimelineCrawler.Path"))
            mock_orjson = stack.enter_context(patch("personaltwilog.TimelineCrawler.orjson"))
            mock_twitter = stack.enter_context(patch("personaltwilog.TimelineCrawler.TwitterAPI"))
            mock_tweet_db = stack.enter_context(patch("personaltwilog.TimelineCrawler.TweetDB"))
            mock_likes_db = stack.enter_context(patch("personaltwilog.TimelineCrawler.LikesDB"))
            mock_media_db = stack.enter_context(patch("personaltwilog.TimelineCrawler.MediaDB"))
            mock_metric_db = stack.enter_context(patch("personaltwilog.TimelineCrawler.MetricDB"))
            mock_external_link_db = stack.enter_context(patch("personaltwilog.TimelineCrawler.ExternalLinkDB"))
            stack.enter_context(freezegun.freeze_time("2023-10-07T01:00:00"))

            sample_config_json = self.get_config_json()
            mock_orjson.loads.side_effect = lambda byte_data: sample_config_json
            crawler = TimelineCrawler()

            crawler.TIMELINE_CACHE_FILE_PATH = "./test/cache/timeline_response.json"
            crawler.LIKES_CACHE_FILE_PATH = "./test/cache/likes_response.json"

            return crawler

    def get_json_dict(self) -> dict:
        return orjson.loads(Path("./test/cache/users_sample.json").read_bytes())

    def test_init(self):
        with ExitStack() as stack:
            mock_logger = stack.enter_context(patch.object(logger, "info"))
            mock_path = stack.enter_context(patch("personaltwilog.TimelineCrawler.Path"))
            mock_orjson = stack.enter_context(patch("personaltwilog.TimelineCrawler.orjson"))
            mock_twitter = stack.enter_context(patch("personaltwilog.TimelineCrawler.TwitterAPI"))
            mock_tweet_db = stack.enter_context(patch("personaltwilog.TimelineCrawler.TweetDB"))
            mock_likes_db = stack.enter_context(patch("personaltwilog.TimelineCrawler.LikesDB"))
            mock_media_db = stack.enter_context(patch("personaltwilog.TimelineCrawler.MediaDB"))
            mock_metric_db = stack.enter_context(patch("personaltwilog.TimelineCrawler.MetricDB"))
            mock_external_link_db = stack.enter_context(patch("personaltwilog.TimelineCrawler.ExternalLinkDB"))
            stack.enter_context(freezegun.freeze_time("2023-10-07T01:00:00"))

            authorize_screen_name = "screen_name_1"
            ct0 = "ct0_1"
            auth_token = "auth_token_1"
            sample_config_json = self.get_config_json()
            mock_orjson.loads.side_effect = lambda byte_data: sample_config_json

            actual = TimelineCrawler()
            mock_twitter.assert_called_once_with(authorize_screen_name, ct0, auth_token)
            mock_tweet_db.assert_called_once_with()
            mock_likes_db.assert_called_once_with()
            mock_media_db.assert_called_once_with()
            mock_metric_db.assert_called_once_with()
            mock_external_link_db.assert_called_once_with()
            self.assertEqual(sample_config_json["twitter_api_client_list"][0], actual.config)
            self.assertEqual(mock_twitter(), actual.twitter)
            self.assertEqual(mock_tweet_db(), actual.tweet_db)
            self.assertEqual(mock_likes_db(), actual.likes_db)
            self.assertEqual(mock_media_db(), actual.media_db)
            self.assertEqual(mock_metric_db(), actual.metric_db)
            self.assertEqual(mock_external_link_db(), actual.external_link_db)
            self.assertEqual("2023-10-07T01:00:00", actual.registered_at)

    def test_timeline_crawl(self):
        with ExitStack() as stack:
            mock_logger = stack.enter_context(patch.object(logger, "info"))
            mock_path = stack.enter_context(patch("personaltwilog.TimelineCrawler.Path"))
            mock_orjson = stack.enter_context(patch("personaltwilog.TimelineCrawler.orjson"))
            crawler = self.get_instance()
            crawler.twitter = (mock_twitter := MagicMock())
            crawler.tweet_db = (mock_tweet_db := MagicMock())
            crawler.media_db = (mock_media_db := MagicMock())
            crawler.metric_db = (mock_metric_db := MagicMock())
            crawler.external_link_db = (mock_external_link_db := MagicMock())
            mock_tweet_db.select_for_max_id.side_effect = lambda screen_name: 100
            mock_twitter.get_user_timeline.side_effect = lambda screen_name, limit, min_id: ["tweet_list_1", ""]
            screen_name = "target_screen_name"

            mock_tweet_parser = stack.enter_context(patch("personaltwilog.TimelineCrawler.TweetParser"))
            mock_media_parser = stack.enter_context(patch("personaltwilog.TimelineCrawler.MediaParser"))
            mock_external_link_parser = stack.enter_context(patch("personaltwilog.TimelineCrawler.ExternalLinkParser"))
            mock_metric_parser = stack.enter_context(patch("personaltwilog.TimelineCrawler.MetricParser"))
            actual = crawler.timeline_crawl(screen_name)
            self.assertEqual(CrawlResultStatus.DONE, actual)

            self.assertEqual([call.__bool__(), call.get_user_timeline(screen_name, 300, 100)], mock_twitter.mock_calls)
            mock_tweet_parser.assert_called_once()
            mock_media_parser.assert_called_once()
            mock_external_link_parser.assert_called_once()
            mock_metric_parser.assert_called_once()
            mock_tweet_db.upsert.assert_called_once()
            mock_media_db.upsert.assert_called_once()
            mock_external_link_db.upsert.assert_called_once()
            mock_metric_db.upsert.assert_called_once()

            mock_twitter.reset_mock()
            mock_tweet_parser.reset_mock()
            mock_media_parser.reset_mock()
            mock_external_link_parser.reset_mock()
            mock_metric_parser.reset_mock()
            mock_tweet_db.reset_mock()
            mock_media_db.reset_mock()
            mock_external_link_db.reset_mock()
            mock_metric_db.reset_mock()

            mock_twitter.get_user_timeline.side_effect = lambda screen_name, limit, min_id: [""]
            actual = crawler.timeline_crawl(screen_name)
            self.assertEqual(CrawlResultStatus.NO_UPDATE, actual)
    
            self.assertEqual([call.__bool__(), call.get_user_timeline(screen_name, 300, 100)], mock_twitter.mock_calls)
            mock_tweet_parser.assert_not_called()
            mock_media_parser.assert_not_called()
            mock_external_link_parser.assert_not_called()
            mock_metric_parser.assert_not_called()
            mock_tweet_db.assert_not_called()
            mock_media_db.assert_not_called()
            mock_external_link_db.assert_not_called()
            mock_metric_db.assert_not_called()

    def test_likes_crawl(self):
        with ExitStack() as stack:
            mock_logger = stack.enter_context(patch.object(logger, "info"))
            mock_path = stack.enter_context(patch("personaltwilog.TimelineCrawler.Path"))
            mock_orjson = stack.enter_context(patch("personaltwilog.TimelineCrawler.orjson"))
            crawler = self.get_instance()
            crawler.twitter = (mock_twitter := MagicMock())
            crawler.likes_db = (mock_likes_db := MagicMock())
            crawler.media_db = (mock_media_db := MagicMock())
            crawler.external_link_db = (mock_external_link_db := MagicMock())
            mock_likes_db.select_for_max_id.side_effect = lambda screen_name: 100
            mock_twitter.get_likes.side_effect = lambda screen_name, limit, min_id: ["tweet_list_1", ""]
            screen_name = "target_screen_name"

            mock_likes_parser = stack.enter_context(patch("personaltwilog.TimelineCrawler.LikesParser"))
            mock_media_parser = stack.enter_context(patch("personaltwilog.TimelineCrawler.MediaParser"))
            mock_external_link_parser = stack.enter_context(patch("personaltwilog.TimelineCrawler.ExternalLinkParser"))
            actual = crawler.likes_crawl(screen_name)
            self.assertEqual(CrawlResultStatus.DONE, actual)

            self.assertEqual([
                call.__bool__(),
                call.get_likes(screen_name, 300, 100),
                call.get_user_id(screen_name),
                call.get_user_name(screen_name),
            ], mock_twitter.mock_calls)
            mock_likes_parser.assert_called_once()
            mock_media_parser.assert_called_once()
            mock_external_link_parser.assert_called_once()
            mock_likes_db.upsert.assert_called_once()
            mock_media_db.upsert.assert_called_once()
            mock_external_link_db.upsert.assert_called_once()

            mock_twitter.reset_mock()
            mock_likes_parser.reset_mock()
            mock_media_parser.reset_mock()
            mock_external_link_parser.reset_mock()
            mock_likes_db.reset_mock()
            mock_media_db.reset_mock()
            mock_external_link_db.reset_mock()

            mock_twitter.get_likes.side_effect = lambda screen_name, limit, min_id: [""]
            actual = crawler.likes_crawl(screen_name)
            self.assertEqual(CrawlResultStatus.NO_UPDATE, actual)
    
            self.assertEqual([call.__bool__(), call.get_likes(screen_name, 300, 100)], mock_twitter.mock_calls)
            mock_likes_parser.assert_not_called()
            mock_media_parser.assert_not_called()
            mock_external_link_parser.assert_not_called()
            mock_likes_db.assert_not_called()
            mock_media_db.assert_not_called()
            mock_external_link_db.assert_not_called()

    def test_run(self):
        with ExitStack() as stack:
            mock_logger = stack.enter_context(patch.object(logger, "info"))
            mock_timeline_crawl = stack.enter_context(patch("personaltwilog.TimelineCrawler.TimelineCrawler.timeline_crawl"))
            mock_likes_crawl = stack.enter_context(patch("personaltwilog.TimelineCrawler.TimelineCrawler.likes_crawl"))
            crawler = self.get_instance()

            actual = crawler.run()
            self.assertEqual(None, actual)
            mock_timeline_crawl.assert_called_once()
            mock_likes_crawl.assert_called_once()

            mock_timeline_crawl.reset_mock()
            mock_likes_crawl.reset_mock()

            crawler.config["target"][0]["status"] = "disable"
            actual = crawler.run()
            self.assertEqual(None, actual)
            mock_timeline_crawl.assert_not_called()
            mock_likes_crawl.assert_not_called()


if __name__ == "__main__":
    if sys.argv:
        del sys.argv[1:]
    unittest.main(warnings="ignore")
