import sys
import unittest

from personal_twilog.db.model import Tweet


class TestTweet(unittest.TestCase):
    def _make_record_dict(
        self,
        index: int = 0,
        is_retweet: bool = False,
        is_quote: bool = False,
        has_media: bool = False,
        has_external_link: bool = False,
    ) -> dict:
        args_dict = {
            "tweet_id": f"{index}",
            "tweet_text": f"tweet_text_{index}",
            "tweet_via": f"tweet_via_{index}",
            "tweet_url": f"tweet_url_{index}",
            "user_id": f"user_id_{index}",
            "user_name": f"user_name_{index}",
            "screen_name": f"screen_name_{index}",
            "is_retweet": is_retweet,
            "retweet_tweet_id": f"retweet_tweet_id_{index}",
            "is_quote": is_quote,
            "quote_tweet_id": f"quote_tweet_id_{index}",
            "has_media": has_media,
            "has_external_link": has_external_link,
            "created_at": f"created_at_{index}",
            "appeared_at": f"appeared_at_{index}",
            "registered_at": f"registered_at_{index}",
        }
        return args_dict

    def test_init(self):
        record_dict = self._make_record_dict()
        instance = Tweet(**record_dict)
        self.assertEqual(record_dict["tweet_id"], instance.tweet_id)
        self.assertEqual(record_dict["tweet_text"], instance.tweet_text)
        self.assertEqual(record_dict["tweet_via"], instance.tweet_via)
        self.assertEqual(record_dict["tweet_url"], instance.tweet_url)
        self.assertEqual(record_dict["user_id"], instance.user_id)
        self.assertEqual(record_dict["user_name"], instance.user_name)
        self.assertEqual(record_dict["screen_name"], instance.screen_name)
        self.assertEqual(record_dict["is_retweet"], instance.is_retweet)
        self.assertEqual(record_dict["retweet_tweet_id"], instance.retweet_tweet_id)
        self.assertEqual(record_dict["is_quote"], instance.is_quote)
        self.assertEqual(record_dict["quote_tweet_id"], instance.quote_tweet_id)
        self.assertEqual(record_dict["has_media"], instance.has_media)
        self.assertEqual(record_dict["has_external_link"], instance.has_external_link)
        self.assertEqual(record_dict["created_at"], instance.created_at)
        self.assertEqual(record_dict["appeared_at"], instance.appeared_at)
        self.assertEqual(record_dict["registered_at"], instance.registered_at)

    def test_create(self):
        record_dict = self._make_record_dict()
        instance = Tweet.create(record_dict)
        self.assertEqual(record_dict, instance.to_dict())

        with self.assertRaises(ValueError):
            instance = Tweet.create("invalid")

    def test_repr(self):
        record_dict = self._make_record_dict()
        instance = Tweet.create(record_dict)
        actual = repr(instance)
        tweet_id = record_dict["tweet_id"]
        screen_name = record_dict["screen_name"]
        expect = f"<Tweet(id='{tweet_id}', screen_name='{screen_name}')>"
        self.assertEqual(expect, actual)

    def test_eq(self):
        record_dict = self._make_record_dict(0)
        instance_1 = Tweet.create(record_dict)
        instance_2 = Tweet.create(record_dict)
        self.assertTrue(instance_1 == instance_2)

        record_dict = self._make_record_dict(1)
        instance_1 = Tweet.create(record_dict)
        self.assertFalse(instance_1 == instance_2)

    def test_to_dict(self):
        record_dict = self._make_record_dict()
        instance = Tweet.create(record_dict)
        self.assertEqual(record_dict, instance.to_dict())


if __name__ == "__main__":
    if sys.argv:
        del sys.argv[1:]
    unittest.main(warnings="ignore")
