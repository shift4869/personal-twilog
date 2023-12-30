from abc import ABCMeta, abstractmethod
from typing import Any

from sqlalchemy import create_engine
from sqlalchemy.pool import StaticPool

from personaltwilog.db.model import Base as ModelBase
from personaltwilog.util import Result


class Base(metaclass=ABCMeta):
    def __init__(self, db_path: str = "timeline.db") -> None:
        self.db_path = db_path
        self.db_url = f"sqlite:///{self.db_path}"

        self.engine = create_engine(
            self.db_url,
            echo=False,
            poolclass=StaticPool,
            # pool_recycle=5,
            connect_args={
                "timeout": 30,
                "check_same_thread": False,
            },
        )
        ModelBase.metadata.create_all(self.engine)

    @abstractmethod
    def select(self) -> list[Any]:
        raise NotImplementedError

    @abstractmethod
    def upsert(self, record: list[dict]) -> Result:
        raise NotImplementedError


if __name__ == "__main__":
    pass
