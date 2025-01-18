import sys
import unittest

from sqlalchemy.orm import sessionmaker

from personal_twilog.db.metric_db import MetricDB
from personal_twilog.db.model import Metric
from personal_twilog.util import Result


class TestMetricDB(unittest.TestCase):
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

    def _get_instance(self) -> MetricDB:
        db_path = ":memory:"
        instance = MetricDB(db_path)
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
            r = Metric.create(self._make_record_dict(i))
            session.add(r)
        session.commit()
        session.close()

        expect = []
        for i in range(5):
            r = Metric.create(self._make_record_dict(i))
            expect.append(r)
        actual = instance.select()

        self.assertEqual(expect, actual)

    def test_upsert(self):
        instance = self._get_instance()
        Session = sessionmaker(bind=instance.engine, autoflush=False)
        session = Session()
        for i in range(5):
            r = Metric.create(self._make_record_dict(i))
            session.add(r)
        session.commit()
        session.close()

        # update
        record = self._make_record_dict(0)
        record["status_count"] = record["status_count"] + 1

        actual = instance.upsert([record])
        actual = instance.select()[0].to_dict()
        expect = record
        self.assertEqual(Result.success, actual)
        self.assertEqual(expect, actual)

        # insert
        record = self._make_record_dict(5)
        actual = instance.upsert([record])
        actual = instance.select()[5].to_dict()
        expect = self._make_record_dict(5)
        self.assertEqual(Result.success, actual)
        self.assertEqual(expect, actual)

        # 引数に辞書でないものが存在する
        record = self._make_record_dict(0)
        actual = instance.upsert([record, "invalid"])
        self.assertEqual(Result.failed, actual)

        # 空リスト指定 -> 0レコードのupsert完了とみなして正常終了扱い
        actual = instance.upsert([])
        self.assertEqual(Result.success, actual)

        # 引数がリストでない
        actual = instance.upsert("invalid")
        self.assertEqual(Result.failed, actual)


if __name__ == "__main__":
    if sys.argv:
        del sys.argv[1:]
    unittest.main(warnings="ignore")
