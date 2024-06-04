import sys
import unittest
from typing import Any

from mock import patch
from sqlalchemy.pool import StaticPool

from personal_twilog.db.base import Base
from personal_twilog.util import Result


class ConcreteBase(Base):
    def __init__(self, db_path: str = "timeline.db") -> None:
        super().__init__(db_path)

    def select(self) -> list[Any]:
        return ["select()"]

    def upsert(self, record: list[dict]) -> list[Result]:
        return [Result.SUCCESS]


class TestBase(unittest.TestCase):
    def test_init(self):
        mock_create_engine = self.enterContext(patch("personal_twilog.db.base.create_engine"))
        mock_create_all = self.enterContext(patch("personal_twilog.db.base.ModelBase.metadata.create_all"))
        mock_create_engine.return_value = "create_engine()"

        db_path = "timeline.db"
        db_url = f"sqlite:///{db_path}"
        instance = ConcreteBase(db_path)

        self.assertEqual(db_path, instance.db_path)
        self.assertEqual(db_url, instance.db_url)
        mock_create_engine.assert_called_once_with(
            db_url,
            echo=False,
            poolclass=StaticPool,
            connect_args={
                "timeout": 30,
                "check_same_thread": False,
            },
        )
        mock_create_all.assert_called_once_with("create_engine()")

        self.assertEqual(["select()"], instance.select())
        self.assertEqual([Result.SUCCESS], instance.upsert([]))


if __name__ == "__main__":
    if sys.argv:
        del sys.argv[1:]
    unittest.main(warnings="ignore")
