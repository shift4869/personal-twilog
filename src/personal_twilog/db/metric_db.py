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
                p.min_appeared_at = r.min_appeared_at
                p.max_appeared_at = r.max_appeared_at
                p.duration_days = r.duration_days
                p.count_all = r.count_all
                p.appeared_days = r.appeared_days
                p.non_appeared_days = r.non_appeared_days
                p.average_tweet_by_day = r.average_tweet_by_day
                p.max_tweet_num_by_day = r.max_tweet_num_by_day
                p.max_tweet_day_by_day = r.max_tweet_day_by_day
                p.tweet_length_sum = r.tweet_length_sum
                p.tweet_length_by_count = r.tweet_length_by_count
                p.tweet_length_by_day = r.tweet_length_by_day
                p.communication_ratio = r.communication_ratio
                p.increase_following_by_day = r.increase_following_by_day
                p.increase_followers_by_day = r.increase_followers_by_day
                p.ff_ratio = r.ff_ratio
                p.ff_ratio_inverse = r.ff_ratio_inverse
                p.available_following = r.available_following
                p.rest_available_following = r.rest_available_following
                # p.registered_at = r.registered_at

        session.commit()
        session.close()
        return Result.success
