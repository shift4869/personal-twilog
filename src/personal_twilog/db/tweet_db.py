from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm.exc import NoResultFound
from sqlalchemy.sql import func

from personal_twilog.db.base import Base
from personal_twilog.db.model import Tweet
from personal_twilog.util import Result


class TweetDB(Base):
    def __init__(self, db_path: str = "timeline.db") -> None:
        super().__init__(db_path)

    def select(self) -> list[dict]:
        Session = sessionmaker(bind=self.engine, autoflush=False)
        session = Session()
        result = session.query(Tweet).all()
        session.close()
        return result

    def select_for_max_id(self, screen_name: str) -> int:
        Session = sessionmaker(bind=self.engine, autoflush=False)
        session = Session()
        r = session.query(func.max(Tweet.tweet_id).filter(Tweet.screen_name == screen_name).label("max_id_str")).one()
        session.close()
        result = r.max_id_str or 0
        return int(result)

    def upsert(self, record: list[dict]) -> Result:
        """upsert

        Args:
            record (list[dict]): レコード辞書のリスト

        Returns:
            Result: upsert に成功したなら Result.success, そうでないなら Result.failed
        """
        if not isinstance(record, list):
            return Result.failed
        if record == []:
            # 空リストは0レコードupsert完了とみなして正常終了扱い
            return Result.success

        all_dict_flag = all([isinstance(r, dict) for r in record])
        if not all_dict_flag:
            return Result.failed

        record_list: list[Tweet] = [Tweet.create(r) for r in record]

        Session = sessionmaker(bind=self.engine, autoflush=False)
        session = Session()

        for r in record_list:
            try:
                q = session.query(Tweet).filter(Tweet.tweet_id == r.tweet_id).with_for_update()
                p = q.one()
            except NoResultFound:
                # INSERT
                session.add(r)
            else:
                # UPDATE
                # idと日付関係以外を更新する
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
                p.has_external_link = r.has_external_link
                # p.created_at = r.created_at
                # p.appeared_at = r.appeared_at
                # p.registered_at = r.registered_at

        session.commit()
        session.close()
        return Result.success
