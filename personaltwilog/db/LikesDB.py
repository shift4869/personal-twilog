# coding: utf-8
from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm.exc import NoResultFound
from sqlalchemy.sql import func

from personaltwilog.db.Base import Base
from personaltwilog.db.Model import Likes


class LikesDB(Base):
    def __init__(self, db_path: str = "timeline.db"):
        super().__init__(db_path)

    def select(self):
        Session = sessionmaker(bind=self.engine, autoflush=False)
        session = Session()
        result = session.query(Likes).all()
        session.close()
        return result

    def select_for_max_id(self) -> int:
        Session = sessionmaker(bind=self.engine, autoflush=False)
        session = Session()
        r = session.query(Likes).order_by(Likes.id.desc()).first()
        session.close()
        result = r.tweet_id or 0
        return int(result)

    def upsert(self, record: Likes | list[dict]) -> list[int]:
        """upsert

        Args:
            record (Likes | list[dict]): 投入レコード、またはレコード辞書のリスト

        Returns:
            list[int]: レコードに対応した投入結果のリスト
                       追加したレコードは0、更新したレコードは1が入る
        """
        result: list[int] = []
        record_list: list[Likes] = []
        if isinstance(record, Likes):
            record_list = [record]
        elif isinstance(record, list):
            if len(record) == 0:
                return []
            if not isinstance(record[0], dict):
                return []
            record_list = [Likes.create(r) for r in record]

        Session = sessionmaker(bind=self.engine, autoflush=False)
        session = Session()

        for r in record_list:
            try:
                q = session.query(Likes).filter(Likes.tweet_id == r.tweet_id).with_for_update()
                p = q.one()
            except NoResultFound:
                # INSERT
                session.add(r)
                result.append(0)
            else:
                # UPDATE
                # id以外を更新する
                p.tweet_id = r.tweet_id
                p.tweet_text = r.tweet_text
                p.tweet_via = r.tweet_via
                p.tweet_url = r.tweet_url
                p.user_id = r.user_id
                p.user_name = r.user_name
                p.screen_name = r.screen_name
                p.is_retweet = r.is_retweet
                p.retweet_tweet_id = r.retweet_tweet_id
                p.is_quote = r.is_quote
                p.quote_tweet_id = r.quote_tweet_id
                p.has_media = r.has_media
                p.created_at = r.created_at
                p.appeared_at = r.appeared_at
                p.registered_at = r.registered_at
                result.append(1)

        session.commit()
        session.close()
        return result
