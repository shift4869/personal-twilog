import re
import sys
import unittest
from datetime import datetime, timedelta

from mock import MagicMock, patch

from personal_twilog.db.tweet_db import TweetDB
from personal_twilog.stats.timeline_stats import TimelineStats


class TestTimelineStats(unittest.TestCase):
    def _make_metric_parsed_dict(self, index: int = 0) -> dict:
        status_count: int = 200
        favorite_count: int = int(status_count * 0.8)
        media_count: int = int(status_count * 0.7)
        following_count: int = 500
        followers_count: int = 100
        args_dict = {
            "screen_name": f"screen_name_{index}",
            "status_count": status_count,
            "favorite_count": favorite_count,
            "media_count": media_count,
            "following_count": following_count,
            "followers_count": followers_count,
            "registered_at": f"registered_at_{index}",
        }
        return args_dict

    def _make_stats_record_dict(self, index: int = 0) -> dict:
        metric_parsed_dict = self._make_metric_parsed_dict(index)
        status_count: int = metric_parsed_dict["status_count"]
        favorite_count: int = metric_parsed_dict["favorite_count"]
        media_count: int = metric_parsed_dict["media_count"]
        following_count: int = metric_parsed_dict["following_count"]
        followers_count: int = metric_parsed_dict["followers_count"]

        min_appeared_at: str = "2025-01-12T22:34:46"
        max_appeared_at: str = "2025-01-17T21:06:56"
        duration_timedelta: timedelta = datetime.fromisoformat(max_appeared_at) - datetime.fromisoformat(
            min_appeared_at
        )
        duration_days: int = duration_timedelta.days

        count_all: int = status_count // 2
        appeared_days: int = duration_days
        non_appeared_days: int = duration_days - appeared_days
        average_tweet_by_day = float(count_all / appeared_days)
        max_tweet_num_by_day = average_tweet_by_day
        max_tweet_day_by_day = datetime.fromisoformat(max_appeared_at).strftime("%Y-%m-%d")

        tweet_str_by_day: int = 25
        tweet_length_sum: int = count_all * tweet_str_by_day
        tweet_length_by_count: float = tweet_length_sum / count_all
        tweet_length_by_day: float = tweet_length_sum / appeared_days

        communication_ratio: int = 50  # 50%

        increase_following_by_day: float = following_count / duration_days
        increase_followers_by_day: float = followers_count / duration_days
        ff_ratio: float = followers_count / following_count
        ff_ratio_inverse: float = 1.0 / ff_ratio
        available_following: int = max(5000, round(followers_count * 1.1))
        rest_available_following: int = available_following - following_count
        args_dict = {
            "screen_name": f"screen_name_{index}",
            "status_count": status_count,
            "favorite_count": favorite_count,
            "media_count": media_count,
            "following_count": following_count,
            "followers_count": followers_count,
            "min_appeared_at": min_appeared_at,
            "max_appeared_at": max_appeared_at,
            "duration_days": duration_days,
            "count_all": count_all,
            "appeared_days": appeared_days,
            "non_appeared_days": non_appeared_days,
            "average_tweet_by_day": average_tweet_by_day,
            "max_tweet_num_by_day": max_tweet_num_by_day,
            "max_tweet_day_by_day": max_tweet_day_by_day,
            "tweet_length_sum": tweet_length_sum,
            "tweet_length_by_count": tweet_length_by_count,
            "tweet_length_by_day": tweet_length_by_day,
            "communication_ratio": communication_ratio,
            "increase_following_by_day": increase_following_by_day,
            "increase_followers_by_day": increase_followers_by_day,
            "ff_ratio": ff_ratio,
            "ff_ratio_inverse": ff_ratio_inverse,
            "available_following": available_following,
            "rest_available_following": rest_available_following,
            "registered_at": f"registered_at_{index}",
        }
        return args_dict

    def _make_execute(self, stats_record_dict: dict) -> MagicMock:
        r = MagicMock(name="make_execute")

        def _dispatch(key: str) -> str | int | float:
            key = str(key)
            if re.search(r"min\(appeared_at\)", key):
                return [stats_record_dict["min_appeared_at"]]
            if re.search(r"max\(appeared_at\)", key):
                return [stats_record_dict["max_appeared_at"]]
            if re.search(r"count\(\*\)", key):
                return [stats_record_dict["count_all"]]
            if re.search(r"count\(appeared_days\)", key):
                return [
                    stats_record_dict["appeared_days"],
                    stats_record_dict["average_tweet_by_day"],
                    stats_record_dict["max_tweet_num_by_day"],
                    stats_record_dict["max_tweet_day_by_day"],
                ]
            if re.search(r"sum\(string_length\)", key):
                return [stats_record_dict["tweet_length_sum"]]
            if re.search(r"count\(tweet_text\)", key):
                count_all = stats_record_dict["count_all"]
                communication_ratio: float = float(stats_record_dict["communication_ratio"])
                communication_tweet_num: int = int(count_all * (communication_ratio / 100.0))
                return [communication_tweet_num]

        def _make_execute_text(text: str) -> MagicMock:
            rt = MagicMock()
            rt.one.return_value = _dispatch(text)
            return rt

        r.execute.side_effect = _make_execute_text
        return r

    def test_init(self):
        mock_get_stats = self.enterContext(patch("personal_twilog.stats.timeline_stats.TimelineStats.get_stats"))
        mock_tweet_db = MagicMock(spec=TweetDB)
        metric_parsed_dict = self._make_metric_parsed_dict()

        instance = TimelineStats(metric_parsed_dict, mock_tweet_db)
        mock_get_stats.assert_called_once_with()

        self.assertEqual(metric_parsed_dict, instance.metric_parsed_dict)
        self.assertEqual(mock_tweet_db, instance.tweet_db)
        self.assertEqual(metric_parsed_dict["registered_at"], instance.registered_at)
        self.assertEqual(metric_parsed_dict["screen_name"], instance.screen_name)
        self.assertEqual(mock_get_stats.return_value, instance.stats)

        with self.assertRaises(ValueError):
            instance = TimelineStats(["invalid_args_dict"], mock_tweet_db)
        with self.assertRaises(ValueError):
            instance = TimelineStats(metric_parsed_dict, "invalid_tweet_db")

    def test_get_stats(self):
        stats_record_dict = self._make_stats_record_dict()
        mock_session = self.enterContext(patch("personal_twilog.stats.timeline_stats.sessionmaker"))
        mock_execute = self._make_execute(stats_record_dict)
        mock_tweet_db = MagicMock(spec=TweetDB)
        mock_tweet_db.engine = "engine"

        metric_parsed_dict = self._make_metric_parsed_dict()
        mock_session.return_value.side_effect = lambda: mock_execute

        actual = TimelineStats(metric_parsed_dict, mock_tweet_db).stats
        self.assertEqual(stats_record_dict, actual)

    def test_to_dict(self):
        stats_record_dict = self._make_stats_record_dict()
        mock_session = self.enterContext(patch("personal_twilog.stats.timeline_stats.sessionmaker"))
        mock_execute = self._make_execute(stats_record_dict)
        mock_tweet_db = MagicMock(spec=TweetDB)
        mock_tweet_db.engine = "engine"

        metric_parsed_dict = self._make_metric_parsed_dict()
        mock_session.return_value.side_effect = lambda: mock_execute

        actual = TimelineStats(metric_parsed_dict, mock_tweet_db).to_dict()
        self.assertEqual(stats_record_dict, actual)


if __name__ == "__main__":
    if sys.argv:
        del sys.argv[1:]
    unittest.main(warnings="ignore")
