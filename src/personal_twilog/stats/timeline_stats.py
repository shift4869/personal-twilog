from datetime import datetime, timedelta

from sqlalchemy import text
from sqlalchemy.orm import sessionmaker

from personal_twilog.db.tweet_db import TweetDB


class TimelineStats:
    def __init__(self, metric_parsed_dict: dict, tweet_db: TweetDB) -> None:
        match metric_parsed_dict:
            case {
                "screen_name": screen_name,
                "status_count": status_count,
                "favorite_count": favorite_count,
                "media_count": media_count,
                "following_count": following_count,
                "followers_count": followers_count,
                "registered_at": registered_at,
            }:
                pass
            case _:
                raise ValueError("Unmatch metric_parsed_dict.")
        if not isinstance(tweet_db, TweetDB):
            raise ValueError("tweet_db must be TweetDB.")

        self.metric_parsed_dict = metric_parsed_dict
        self.tweet_db = tweet_db
        self.registered_at = metric_parsed_dict["registered_at"]
        self.screen_name = metric_parsed_dict["screen_name"]
        self.stats = self.get_stats()

    def get_stats(self) -> dict:
        Session = sessionmaker(bind=self.tweet_db.engine, autoflush=False)
        session = Session()

        min_appeared_at_str: str = session.execute(
            text(f"SELECT min(appeared_at) FROM Tweet WHERE screen_name = '{self.screen_name}';")
        ).one()[0]
        min_appeared_at = datetime.fromisoformat(min_appeared_at_str)
        max_appeared_at_str: str = session.execute(
            text(f"SELECT max(appeared_at) FROM Tweet WHERE screen_name = '{self.screen_name}';")
        ).one()[0]
        max_appeared_at = datetime.fromisoformat(max_appeared_at_str)
        duration_timedelta: timedelta = max_appeared_at - min_appeared_at
        duration_days: int = duration_timedelta.days

        count_all: int = session.execute(
            text(f"SELECT count(*) FROM Tweet WHERE screen_name = '{self.screen_name}';")
        ).one()[0]

        days_sql = f"""
            SELECT 
                count(appeared_days), avg(appeared_count), max(appeared_count), appeared_days
            FROM (
                SELECT
                    strftime('%Y-%m-%d', appeared_at) AS appeared_days,
                    count(appeared_at) AS appeared_count
                FROM Tweet WHERE screen_name = '{self.screen_name}'
                GROUP BY strftime('%Y-%m-%d', appeared_at)
            );
        """
        select_days_result = session.execute(text(days_sql)).one()
        appeared_days: int = select_days_result[0]
        non_appeared_days: int = duration_days - appeared_days
        average_tweet_by_day: float = select_days_result[1]
        max_tweet_num_by_day: int = select_days_result[2]
        max_tweet_day_by_day: str = select_days_result[3]

        tweet_length_sum_sql = f"""
            SELECT 
                sum(string_length)
            FROM (
                SELECT
                    length(tweet_text) AS string_length
                FROM Tweet WHERE screen_name = '{self.screen_name}'
            );
        """
        tweet_length_sum: int = session.execute(text(tweet_length_sum_sql)).one()[0]
        tweet_length_by_count: float = tweet_length_sum / count_all
        tweet_length_by_day: float = tweet_length_sum / appeared_days

        communication_tweet_num_sql = f"""
            SELECT
                count(tweet_text) AS tweet_num
            FROM Tweet
            WHERE
                screen_name = '{self.screen_name}'
                AND tweet_text LIKE '%@%'
        """
        communication_tweet_num: int = session.execute(text(communication_tweet_num_sql)).one()[0]
        communication_ratio: float = round(communication_tweet_num / count_all * 100.0, 2)

        session.close()

        following_count: int = int(self.metric_parsed_dict["following_count"])
        followers_count: int = int(self.metric_parsed_dict["followers_count"])
        increase_following_by_day: float = following_count / duration_days
        increase_followers_by_day: float = followers_count / duration_days
        ff_ratio: float = followers_count / following_count
        ff_ratio_inverse: float = 1.0 / ff_ratio
        available_following: int = max(5000, round(followers_count * 1.1))
        rest_available_following: int = available_following - following_count

        stats_dict = {
            "min_appeared_at": min_appeared_at_str,
            "max_appeared_at": max_appeared_at_str,
            "duration_days": duration_days,
            "count_all": count_all,
            "appeared_days": appeared_days,
            "non_appeared_days": non_appeared_days,
            "average_tweet_by_day": average_tweet_by_day,
            "max_tweet_num_by_day": max_tweet_num_by_day,
            "max_tweet_day_by_day": max_tweet_day_by_day,
            "tweet_length_sum": tweet_length_sum,
            "tweet_length_by_count": tweet_length_by_count,
            "tweet_length_by_day": tweet_length_by_day,
            "communication_ratio": communication_ratio,
            "increase_following_by_day": increase_following_by_day,
            "increase_followers_by_day": increase_followers_by_day,
            "ff_ratio": ff_ratio,
            "ff_ratio_inverse": ff_ratio_inverse,
            "available_following": available_following,
            "rest_available_following": rest_available_following,
        }
        return self.metric_parsed_dict | stats_dict

    def to_dict(self) -> dict:
        return self.stats


if __name__ == "__main__":
    import pprint

    registered_at = datetime.now().replace(microsecond=0).isoformat()
    target_screen_name = "_shift4869"
    metric_parsed_dict = {
        "screen_name": target_screen_name,
        "status_count": 100,
        "favorite_count": 100,
        "media_count": 100,
        "following_count": 200,
        "followers_count": 100,
        "registered_at": registered_at,
    }
    tweet_db = TweetDB()

    timeline_stats = TimelineStats(metric_parsed_dict, tweet_db)
    stats = timeline_stats.to_dict()
    pprint.pprint(stats)
