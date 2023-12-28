from abc import ABCMeta, abstractmethod

from sqlalchemy import create_engine
from sqlalchemy.pool import StaticPool

from personaltwilog.db.model import Base as ModelBase


class Base(metaclass=ABCMeta):
    def __init__(self, db_path: str = "timeline.db"):
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
    def select(self):
        return []

    @abstractmethod
    def upsert(self, record):
        return []


if __name__ == "__main__":
    pass
