import sys
import unittest

from personaltwilog.db.model import Media


class TestMedia(unittest.TestCase):
    def _make_record_dict(self, index: int = 0) -> dict:
        args_dict = {
            "tweet_id": f"{index}",
            "tweet_text": f"tweet_text_{index}",
            "tweet_via": f"tweet_via_{index}",
            "tweet_url": f"tweet_url_{index}",
            "media_filename": f"media_filename_{index}",
            "media_url": f"media_url_{index}",
            "media_thumbnail_url": f"media_thumbnail_url_{index}",
            "media_type": f"media_type_{index}",
            "media_size": index,
            "created_at": f"created_at_{index}",
            "appeared_at": f"appeared_at_{index}",
            "registered_at": f"registered_at_{index}",
        }
        return args_dict

    def test_init(self):
        record_dict = self._make_record_dict()
        instance = Media(**record_dict)
        self.assertEqual(record_dict["tweet_id"], instance.tweet_id)
        self.assertEqual(record_dict["tweet_text"], instance.tweet_text)
        self.assertEqual(record_dict["tweet_via"], instance.tweet_via)
        self.assertEqual(record_dict["tweet_url"], instance.tweet_url)
        self.assertEqual(record_dict["media_filename"], instance.media_filename)
        self.assertEqual(record_dict["media_url"], instance.media_url)
        self.assertEqual(record_dict["media_thumbnail_url"], instance.media_thumbnail_url)
        self.assertEqual(record_dict["media_type"], instance.media_type)
        self.assertEqual(record_dict["media_size"], instance.media_size)
        self.assertEqual(record_dict["created_at"], instance.created_at)
        self.assertEqual(record_dict["appeared_at"], instance.appeared_at)
        self.assertEqual(record_dict["registered_at"], instance.registered_at)

    def test_create(self):
        record_dict = self._make_record_dict()
        instance = Media.create(record_dict)
        self.assertEqual(record_dict, instance.to_dict())

        with self.assertRaises(ValueError):
            instance = Media.create("invalid")

    def test_repr(self):
        record_dict = self._make_record_dict()
        instance = Media.create(record_dict)
        actual = repr(instance)
        tweet_id = record_dict["tweet_id"]
        media_filename = record_dict["media_filename"]
        expect = f"<Media(tweet_id='{tweet_id}', media_filename='{media_filename}')>"
        self.assertEqual(expect, actual)

    def test_eq(self):
        record_dict = self._make_record_dict(0)
        instance_1 = Media.create(record_dict)
        instance_2 = Media.create(record_dict)
        self.assertTrue(instance_1 == instance_2)

        record_dict = self._make_record_dict(1)
        instance_1 = Media.create(record_dict)
        self.assertFalse(instance_1 == instance_2)

    def test_to_dict(self):
        record_dict = self._make_record_dict()
        instance = Media.create(record_dict)
        self.assertEqual(record_dict, instance.to_dict())


if __name__ == "__main__":
    if sys.argv:
        del sys.argv[1:]
    unittest.main(warnings="ignore")
