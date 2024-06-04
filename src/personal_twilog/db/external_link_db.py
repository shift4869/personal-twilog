from sqlalchemy import and_
from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm.exc import NoResultFound

from personal_twilog.db.base import Base
from personal_twilog.db.model import ExternalLink
from personal_twilog.util import Result


class ExternalLinkDB(Base):
    def __init__(self, db_path: str = "timeline.db") -> None:
        super().__init__(db_path)

    def select(self) -> list[dict]:
        Session = sessionmaker(bind=self.engine, autoflush=False)
        session = Session()
        result = session.query(ExternalLink).all()
        session.close()
        return result

    def upsert(self, record: list[dict]) -> Result:
        """upsert

        Args:
            record (list[dict]): レコード辞書のリスト

        Returns:
            Result: upsert に成功したなら Result.SUCCESS, そうでないなら Result.FAILED
        """
        if not isinstance(record, list):
            return Result.FAILED
        if record == []:
            # 空リストは0レコードupsert完了とみなして正常終了扱い
            return Result.SUCCESS

        all_dict_flag = all([isinstance(r, dict) for r in record])
        if not all_dict_flag:
            return Result.FAILED

        record_list: list[ExternalLink] = [ExternalLink.create(r) for r in record]

        Session = sessionmaker(bind=self.engine, autoflush=False)
        session = Session()

        for r in record_list:
            try:
                q = (
                    session.query(ExternalLink)
                    .filter(and_(ExternalLink.tweet_id == r.tweet_id, ExternalLink.registered_at == r.registered_at))
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
                p.external_link_url = r.external_link_url
                p.external_link_type = r.external_link_type
                # p.created_at = r.created_at
                # p.appeared_at = r.appeared_at
                # p.registered_at = r.registered_at

        session.commit()
        session.close()
        return Result.SUCCESS
