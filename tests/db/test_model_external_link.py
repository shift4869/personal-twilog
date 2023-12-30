import sys
import unittest

from personaltwilog.db.model import ExternalLink


class TestExternalLink(unittest.TestCase):
    def _make_record_dict(self, index: int = 0) -> dict:
        args_dict = {
            "tweet_id": f"{index}",
            "tweet_text": f"tweet_text_{index}",
            "tweet_via": f"tweet_via_{index}",
            "tweet_url": f"tweet_url_{index}",
            "external_link_url": f"external_link_url_{index}",
            "external_link_type": f"external_link_type_{index}",
            "created_at": f"created_at_{index}",
            "appeared_at": f"appeared_at_{index}",
            "registered_at": f"registered_at_{index}",
        }
        return args_dict

    def test_init(self):
        record_dict = self._make_record_dict()
        instance = ExternalLink(**record_dict)
        self.assertEqual(record_dict["tweet_id"], instance.tweet_id)
        self.assertEqual(record_dict["tweet_text"], instance.tweet_text)
        self.assertEqual(record_dict["tweet_via"], instance.tweet_via)
        self.assertEqual(record_dict["tweet_url"], instance.tweet_url)
        self.assertEqual(record_dict["external_link_url"], instance.external_link_url)
        self.assertEqual(record_dict["external_link_type"], instance.external_link_type)
        self.assertEqual(record_dict["created_at"], instance.created_at)
        self.assertEqual(record_dict["appeared_at"], instance.appeared_at)
        self.assertEqual(record_dict["registered_at"], instance.registered_at)

    def test_create(self):
        record_dict = self._make_record_dict()
        instance = ExternalLink.create(record_dict)
        self.assertEqual(record_dict, instance.to_dict())

        with self.assertRaises(ValueError):
            instance = ExternalLink.create("invalid")

    def test_repr(self):
        record_dict = self._make_record_dict()
        instance = ExternalLink.create(record_dict)
        actual = repr(instance)
        external_link_url = record_dict["external_link_url"]
        expect = f"<ExternalLink(external_link_url='{external_link_url}')>"
        self.assertEqual(expect, actual)

    def test_eq(self):
        record_dict = self._make_record_dict(0)
        instance_1 = ExternalLink.create(record_dict)
        instance_2 = ExternalLink.create(record_dict)
        self.assertTrue(instance_1 == instance_2)

        record_dict = self._make_record_dict(1)
        instance_1 = ExternalLink.create(record_dict)
        self.assertFalse(instance_1 == instance_2)

    def test_to_dict(self):
        record_dict = self._make_record_dict()
        instance = ExternalLink.create(record_dict)
        self.assertEqual(record_dict, instance.to_dict())


if __name__ == "__main__":
    if sys.argv:
        del sys.argv[1:]
    unittest.main(warnings="ignore")
