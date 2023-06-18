# coding: utf-8
import re
from typing import Self

from sqlalchemy import asc, or_
from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm.exc import NoResultFound
from sqlalchemy.sql import func

from personaltwilog.db.Base import Base
from personaltwilog.db.Model import Metric


class MetricDB(Base):
    def __init__(self, db_path: str = "timeline.db"):
        super().__init__(db_path)

    def select(self):
        Session = sessionmaker(bind=self.engine, autoflush=False)
        session = Session()
        result = session.query(Metric).all()
        session.close()
        return result

    def upsert(self, record: Metric | list[dict]) -> list[int]:
        """upsert

        Args:
            record (Metric | list[dict]): 投入レコード、またはレコード辞書のリスト

        Returns:
            list[int]: レコードに対応した投入結果のリスト
                       追加したレコードは0、更新したレコードは1が入る
        """
        result: list[int] = []
        record_list: list[Metric] = []
        if isinstance(record, Metric):
            record_list = [record]
        elif isinstance(record, list):
            if len(record) == 0:
                return []
            if not isinstance(record[0], dict):
                return []
            record_list = [Metric.create(r) for r in record]

        Session = sessionmaker(bind=self.engine, autoflush=False)
        session = Session()

        for r in record_list:
            try:
                q = session.query(Metric).filter(Metric.registered_at == r.registered_at).with_for_update()
                p = q.one()
            except NoResultFound:
                # INSERT
                session.add(r)
                result.append(0)
            else:
                # UPDATE
                # idと日付関係以外を更新する
                p.status_count = r.status_count,
                p.favorite_count = r.favorite_count,
                p.media_count = r.media_count,
                p.following_count = r.following_count,
                p.followers_count = r.followers_count,
                # p.registered_at = r.registered_at
                result.append(1)

        session.commit()
        session.close()
        return result
