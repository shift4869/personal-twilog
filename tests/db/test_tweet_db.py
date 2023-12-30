import sys
import unittest

from sqlalchemy.orm import sessionmaker

from personaltwilog.db.tweet_db import TweetDB
from personaltwilog.db.model import Tweet
from personaltwilog.util import Result


class TestTweetDB(unittest.TestCase):
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

    def _get_instance(self) -> TweetDB:
        db_path = ":memory:"
        instance = TweetDB(db_path)
        return instance

    def test_init(self):
        db_path = ":memory:"
        instance = self._get_instance()
        self.assertEqual(db_path, instance.db_path)

    def test_select(self):
        instance = self._get_instance()
        Session = sessionmaker(bind=instance.engine, autoflush=False)
        session = Session()
        for i in range(5):
            r = Tweet.create(self._make_record_dict(i))
            session.add(r)
        session.commit()
        session.close()

        expect = []
        for i in range(5):
            r = Tweet.create(self._make_record_dict(i))
            expect.append(r)
        actual = instance.select()

        self.assertEqual(expect, actual)

    def test_select_for_max_id(self):
        instance = self._get_instance()
        Session = sessionmaker(bind=instance.engine, autoflush=False)
        session = Session()
        for i in range(5):
            r = Tweet.create(self._make_record_dict(i))
            r.screen_name = "screen_name"
            session.add(r)
        session.commit()
        session.close()

        expect = 4
        actual = instance.select_for_max_id("screen_name")
        self.assertEqual(expect, actual)

        expect = 0
        actual = instance.select_for_max_id("not_found")
        self.assertEqual(expect, actual)

    def test_upsert(self):
        instance = self._get_instance()
        Session = sessionmaker(bind=instance.engine, autoflush=False)
        session = Session()
        for i in range(5):
            r = Tweet.create(self._make_record_dict(i))
            session.add(r)
        session.commit()
        session.close()

        # update
        record = self._make_record_dict(0)
        record["tweet_text"] = "new_tweet_text"

        actual = instance.upsert([record])
        self.assertEqual(Result.SUCCESS, actual)
        actual = instance.select()[0].to_dict()
        expect = record
        self.assertEqual(expect, actual)

        # insert
        record = self._make_record_dict(5)
        actual = instance.upsert([record])
        self.assertEqual(Result.SUCCESS, actual)
        actual = instance.select()[5].to_dict()
        expect = self._make_record_dict(5)
        self.assertEqual(expect, actual)

        # 引数に辞書でないものが存在する
        record = self._make_record_dict(0)
        actual = instance.upsert([record, "invalid"])
        self.assertEqual(Result.FAILED, actual)

        # 空リスト指定 -> 0レコードのupsert完了とみなして正常終了扱い
        actual = instance.upsert([])
        self.assertEqual(Result.SUCCESS, actual)

        # 引数がリストでない
        actual = instance.upsert("invalid")
        self.assertEqual(Result.FAILED, actual)


if __name__ == "__main__":
    if sys.argv:
        del sys.argv[1:]
    unittest.main(warnings="ignore")
