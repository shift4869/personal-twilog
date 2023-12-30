import sys
import unittest

from personaltwilog.db.model import Metric


class TestMetric(unittest.TestCase):
    def _make_record_dict(self, index: int = 0) -> dict:
        args_dict = {
            "screen_name": f"screen_name_{index}",
            "status_count": index,
            "favorite_count": index,
            "media_count": index,
            "following_count": index,
            "followers_count": index,
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
