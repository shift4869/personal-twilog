# coding: utf-8
import re
from typing import Self

from sqlalchemy import asc, or_
from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm.exc import NoResultFound
from sqlalchemy.sql import func

from personaltwilog.db.Base import Base
from personaltwilog.db.Model import Media


class MediaDB(Base):
    def __init__(self, db_path: str = "timeline.db"):
        super().__init__(db_path)

    def select(self):
        Session = sessionmaker(bind=self.engine, autoflush=False)
        session = Session()
        result = session.query(Media).all()
        session.close()
        return result

    def upsert(self, record: Media | list[dict]) -> list[int]:
        """upsert

        Args:
            record (Media | list[dict]): 投入レコード、またはレコード辞書のリスト

        Returns:
            list[int]: レコードに対応した投入結果のリスト
                       追加したレコードは0、更新したレコードは1が入る
        """
        result: list[int] = []
        record_list: list[Media] = []
        if isinstance(record, Media):
            record_list = [record]
        elif isinstance(record, list):
            if len(record) == 0:
                return []
            if not isinstance(record[0], dict):
                return []
            record_list = [Media.create(r) for r in record]

        Session = sessionmaker(bind=self.engine, autoflush=False)
        session = Session()

        for r in record_list:
            try:
                q = session.query(Media).filter(Media.registered_at == r.registered_at).with_for_update()
                p = q.one()
            except NoResultFound:
                # INSERT
                session.add(r)
                result.append(0)
            else:
                # UPDATE
                # id以外を更新する
                p.tweet_id = r.tweet_id
                p.media_filename = r.media_filename
                p.media_url = r.media_url
                p.media_thumbnail_url = r.media_thumbnail_url
                p.media_type = r.media_type
                p.media_size = r.media_size
                p.created_at = r.created_at
                p.appeared_at = r.appeared_at
                p.registered_at = r.registered_at
                result.append(1)

        session.commit()
        session.close()
        return result
