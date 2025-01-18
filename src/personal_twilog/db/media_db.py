from sqlalchemy import and_
from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm.exc import NoResultFound

from personal_twilog.db.base import Base
from personal_twilog.db.model import Media
from personal_twilog.util import Result


class MediaDB(Base):
    def __init__(self, db_path: str = "timeline.db"):
        super().__init__(db_path)

    def select(self) -> list[dict]:
        Session = sessionmaker(bind=self.engine, autoflush=False)
        session = Session()
        result = session.query(Media).all()
        session.close()
        return result

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

        record_list: list[Media] = [Media.create(r) for r in record]

        Session = sessionmaker(bind=self.engine, autoflush=False)
        session = Session()

        for r in record_list:
            try:
                q = (
                    session.query(Media)
                    .filter(and_(Media.tweet_id == r.tweet_id, Media.registered_at == r.registered_at))
                    .with_for_update()
                )
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
                p.media_filename = r.media_filename
                p.media_url = r.media_url
                p.media_thumbnail_url = r.media_thumbnail_url
                p.media_type = r.media_type
                p.media_size = r.media_size
                # p.created_at = r.created_at
                # p.appeared_at = r.appeared_at
                # p.registered_at = r.registered_at

        session.commit()
        session.close()
        return Result.success
