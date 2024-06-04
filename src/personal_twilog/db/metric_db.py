from sqlalchemy import and_
from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm.exc import NoResultFound

from personal_twilog.db.base import Base
from personal_twilog.db.model import Metric
from personal_twilog.util import Result


class MetricDB(Base):
    def __init__(self, db_path: str = "timeline.db") -> None:
        super().__init__(db_path)

    def select(self) -> list[dict]:
        Session = sessionmaker(bind=self.engine, autoflush=False)
        session = Session()
        result = session.query(Metric).all()
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

        record_list: list[Metric] = [Metric.create(r) for r in record]

        Session = sessionmaker(bind=self.engine, autoflush=False)
        session = Session()

        for r in record_list:
            try:
                q = (
                    session.query(Metric)
                    .filter(and_(Metric.registered_at == r.registered_at, Metric.screen_name == r.screen_name))
                    .with_for_update()
                )
                p = q.one()
            except NoResultFound:
                # INSERT
                session.add(r)
            else:
                # UPDATE
                # idと日付関係以外を更新する
                p.screen_name = r.screen_name
                p.status_count = r.status_count
                p.favorite_count = r.favorite_count
                p.media_count = r.media_count
                p.following_count = r.following_count
                p.followers_count = r.followers_count
                # p.registered_at = r.registered_at

        session.commit()
        session.close()
        return Result.SUCCESS
