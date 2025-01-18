import sys
import unittest

from personal_twilog.db.model import Metric


class TestMetric(unittest.TestCase):
    def _make_record_dict(self, index: int = 0) -> dict:
        args_dict = {
            "screen_name": f"screen_name_{index}",
            "status_count": index,
            "favorite_count": index,
            "media_count": index,
            "following_count": index,
            "followers_count": index,
            "min_appeared_at": "2023-04-02T22:34:46",
            "max_appeared_at": "2025-01-17T21:06:56",
            "duration_days": index,
            "count_all": index,
            "appeared_days": index,
            "non_appeared_days": index,
            "average_tweet_by_day": 1.0,
            "max_tweet_num_by_day": index,
            "max_tweet_day_by_day": "2024-12-06",
            "tweet_length_sum": index,
            "tweet_length_by_count": 1.0,
            "tweet_length_by_day": 1.0,
            "communication_ratio": 1.0,
            "increase_following_by_day": 0.1,
            "increase_followers_by_day": 0.1,
            "ff_ratio": 0.1,
            "ff_ratio_inverse": 1.0,
            "available_following": index,
            "rest_available_following": index,
            "registered_at": f"registered_at_{index}",
        }
        return args_dict

    def test_init(self):
        record_dict = self._make_record_dict()
        instance = Metric(**record_dict)
        self.assertEqual(record_dict["screen_name"], instance.screen_name)
        self.assertEqual(record_dict["status_count"], instance.status_count)
        self.assertEqual(record_dict["favorite_count"], instance.favorite_count)
        self.assertEqual(record_dict["media_count"], instance.media_count)
        self.assertEqual(record_dict["following_count"], instance.following_count)
        self.assertEqual(record_dict["followers_count"], instance.followers_count)
        self.assertEqual(record_dict["min_appeared_at"], instance.min_appeared_at)
        self.assertEqual(record_dict["max_appeared_at"], instance.max_appeared_at)
        self.assertEqual(record_dict["duration_days"], instance.duration_days)
        self.assertEqual(record_dict["count_all"], instance.count_all)
        self.assertEqual(record_dict["appeared_days"], instance.appeared_days)
        self.assertEqual(record_dict["non_appeared_days"], instance.non_appeared_days)
        self.assertEqual(record_dict["average_tweet_by_day"], instance.average_tweet_by_day)
        self.assertEqual(record_dict["max_tweet_num_by_day"], instance.max_tweet_num_by_day)
        self.assertEqual(record_dict["max_tweet_day_by_day"], instance.max_tweet_day_by_day)
        self.assertEqual(record_dict["tweet_length_sum"], instance.tweet_length_sum)
        self.assertEqual(record_dict["tweet_length_by_count"], instance.tweet_length_by_count)
        self.assertEqual(record_dict["tweet_length_by_day"], instance.tweet_length_by_day)
        self.assertEqual(record_dict["communication_ratio"], instance.communication_ratio)
        self.assertEqual(record_dict["increase_following_by_day"], instance.increase_following_by_day)
        self.assertEqual(record_dict["increase_followers_by_day"], instance.increase_followers_by_day)
        self.assertEqual(record_dict["ff_ratio"], instance.ff_ratio)
        self.assertEqual(record_dict["ff_ratio_inverse"], instance.ff_ratio_inverse)
        self.assertEqual(record_dict["available_following"], instance.available_following)
        self.assertEqual(record_dict["rest_available_following"], instance.rest_available_following)
        self.assertEqual(record_dict["registered_at"], instance.registered_at)

    def test_create(self):
        record_dict = self._make_record_dict()
        instance = Metric.create(record_dict)
        self.assertEqual(record_dict, instance.to_dict())

        with self.assertRaises(ValueError):
            instance = Metric.create("invalid")

    def test_repr(self):
        record_dict = self._make_record_dict()
        instance = Metric.create(record_dict)
        actual = repr(instance)
        registered_at = record_dict["registered_at"]
        expect = f"<Metric(registered_at='{registered_at}')>"
        self.assertEqual(expect, actual)

    def test_eq(self):
        record_dict = self._make_record_dict(0)
        instance_1 = Metric.create(record_dict)
        instance_2 = Metric.create(record_dict)
        self.assertTrue(instance_1 == instance_2)

        record_dict = self._make_record_dict(1)
        instance_1 = Metric.create(record_dict)
        self.assertFalse(instance_1 == instance_2)

    def test_to_dict(self):
        record_dict = self._make_record_dict()
        instance = Metric.create(record_dict)
        self.assertEqual(record_dict, instance.to_dict())


if __name__ == "__main__":
    if sys.argv:
        del sys.argv[1:]
    unittest.main(warnings="ignore")
