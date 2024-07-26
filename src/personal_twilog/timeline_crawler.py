import logging.config
from datetime import datetime
from enum import Enum, auto
from logging import INFO, getLogger
from pathlib import Path

import orjson

from personal_twilog.db.external_link_db import ExternalLinkDB
from personal_twilog.db.likes_db import LikesDB
from personal_twilog.db.media_db import MediaDB
from personal_twilog.db.metric_db import MetricDB
from personal_twilog.db.tweet_db import TweetDB
from personal_twilog.parser.external_link_parser import ExternalLinkParser
from personal_twilog.parser.likes_parser import LikesParser
from personal_twilog.parser.media_parser import MediaParser
from personal_twilog.parser.metric_parser import MetricParser
from personal_twilog.parser.tweet_parser import TweetParser
from personal_twilog.stats.timeline_stats import TimelineStats
from personal_twilog.webapi.twitter_api import TwitterAPI

logger = getLogger(__name__)
logger.setLevel(INFO)
DEBUG = False


class CrawlResultStatus(Enum):
    NO_UPDATE = auto()
    DONE = auto()


class TimelineCrawler:
    TIMELINE_CACHE_FILE_PATH = "./cache/timeline_response.json"
    LIKES_CACHE_FILE_PATH = "./cache/likes_response.json"

    def __init__(self) -> None:
        logger.info("TimelineCrawler init -> start")
        CONFIG_FILE_NAME = "./config/config.json"
        config = orjson.loads(Path(CONFIG_FILE_NAME).read_bytes())

        self.config = config["twitter_api_client_list"]

        self.tweet_db = TweetDB()
        self.likes_db = LikesDB()
        self.media_db = MediaDB()
        self.metric_db = MetricDB()
        self.external_link_db = ExternalLinkDB()

        # 各DBで共通に使う registered_at を取得
        self.registered_at = datetime.now().replace(microsecond=0).isoformat()
        logger.info("TimelineCrawler init -> done")

    def timeline_crawl(self, screen_name: str) -> CrawlResultStatus:
        logger.info("TimelineCrawler timeline_crawl -> start")
        logger.info("TimelineCrawler timeline_crawl init -> start")
        # 探索する id_str の下限値を設定
        min_id = self.tweet_db.select_for_max_id(screen_name)
        logger.info(f"Target timeline's screen_name is '{screen_name}'.")
        logger.info(f"Last registered tweet_id is '{min_id}'.")
        logger.info("TimelineCrawler timeline_crawl init -> done")

        # TL取得
        logger.info(f"Getting timeline of '{screen_name}' -> start")
        limit = 300
        tweet_list = []
        if self.twitter:
            tweet_list = self.twitter.get_user_timeline(screen_name, limit, min_id)
            tweet_list = tweet_list[:-1]
            if tweet_list:
                Path(TimelineCrawler.TIMELINE_CACHE_FILE_PATH).write_bytes(
                    orjson.dumps(tweet_list, option=orjson.OPT_INDENT_2)
                )
        else:
            tweet_list = orjson.loads(Path(TimelineCrawler.TIMELINE_CACHE_FILE_PATH).read_bytes())

        if not tweet_list:
            logger.info(f"Getting timeline of '{screen_name}' -> done")
            logger.info(f"No new tweet of '{screen_name}'.")
            logger.info("TimelineCrawler timeline_crawl -> done")
            return CrawlResultStatus.NO_UPDATE
        logger.info(f"Number of new tweet of '{screen_name}' is {len(tweet_list)}.")
        logger.info(f"Getting timeline of '{screen_name}' -> done")

        # Tweet
        logger.info("Tweet table update -> start")
        tweet_dict_list = TweetParser(tweet_list, self.registered_at).parse()
        self.tweet_db.upsert(tweet_dict_list)
        logger.info("Tweet table update -> done")

        # Media
        logger.info("Media table update -> start")
        media_dict_list = MediaParser(tweet_list, self.registered_at).parse()
        self.media_db.upsert(media_dict_list)
        logger.info("Media table update -> done")

        # ExternalLink
        logger.info("ExternalLink table update -> start")
        external_link_dict_list = ExternalLinkParser(tweet_list, self.registered_at).parse()
        self.external_link_db.upsert(external_link_dict_list)
        logger.info("ExternalLink table update -> done")

        # Metric
        logger.info("Metric table update -> start")
        metric_parsed_dict = MetricParser(tweet_list, self.registered_at, screen_name).parse()
        metric_dict = TimelineStats(metric_parsed_dict[0], self.tweet_db).to_dict()
        self.metric_db.upsert([metric_dict])
        logger.info("Metric table update -> done")

        logger.info("TimelineCrawler timeline_crawl -> done")
        return CrawlResultStatus.DONE

    def likes_crawl(self, screen_name: str) -> CrawlResultStatus:
        logger.info("TimelineCrawler likes_crawl -> start")
        logger.info("TimelineCrawler likes_crawl init -> start")
        # 探索する id_str の下限値を設定
        min_id = self.likes_db.select_for_max_id(screen_name)
        logger.info(f"Target Likes's screen_name is '{screen_name}'.")
        logger.info(f"Last registered tweet_id is '{min_id}'.")
        logger.info("TimelineCrawler likes_crawl init -> done")

        # Likes 取得
        logger.info(f"Getting Likes of '{screen_name}' -> start")
        limit = 300
        tweet_list = []
        if self.twitter:
            tweet_list = self.twitter.get_likes(screen_name, limit, min_id)
            tweet_list = tweet_list[:-1]
            if tweet_list:
                Path(TimelineCrawler.LIKES_CACHE_FILE_PATH).write_bytes(
                    orjson.dumps(tweet_list, option=orjson.OPT_INDENT_2)
                )
        else:
            tweet_list = orjson.loads(Path(TimelineCrawler.LIKES_CACHE_FILE_PATH).read_bytes())

        if not tweet_list:
            logger.info(f"Getting Likes of '{screen_name}' -> done")
            logger.info(f"No new tweet of '{screen_name}'.")
            logger.info("TimelineCrawler likes_crawl -> done")
            return CrawlResultStatus.NO_UPDATE
        logger.info(f"Number of new tweet of '{screen_name}' is {len(tweet_list)}.")
        logger.info(f"Getting Likes of '{screen_name}' -> done")

        # Likes
        logger.info("Likes table update -> start")
        user_id = self.twitter.get_user_id(screen_name)
        user_name = self.twitter.get_user_name(screen_name)
        tweet_dict_list = LikesParser(
            tweet_list, self.registered_at, user_id.id_str, user_name.name, screen_name
        ).parse()
        self.likes_db.upsert(tweet_dict_list)
        logger.info("Likes table update -> done")

        # Media
        logger.info("Media table update -> start")
        media_dict_list = MediaParser(tweet_list, self.registered_at).parse()
        self.media_db.upsert(media_dict_list)
        logger.info("Media table update -> done")

        # ExternalLink
        logger.info("ExternalLink table update -> start")
        external_link_dict_list = ExternalLinkParser(tweet_list, self.registered_at).parse()
        self.external_link_db.upsert(external_link_dict_list)
        logger.info("ExternalLink table update -> done")

        # Metric は投入しない

        logger.info("TimelineCrawler likes_crawl -> done")
        return CrawlResultStatus.DONE

    def run(self) -> None:
        logger.info("TimelineCrawler run -> start")
        # authorize_screen_name = self.twitter.authorize_screen_name.name
        # logger.info(f"Authorize screen_name is '{authorize_screen_name}'.")
        target_dicts = self.config
        for target_dict in target_dicts:
            is_enable = "enable" == target_dict["status"]
            screen_name = target_dict["screen_name"]

            if not is_enable:
                logger.info(f"Status is not enable , target screen_name = '{screen_name}' -> skip")
                continue

            ct0 = target_dict["ct0"]
            auth_token = target_dict["auth_token"]

            if not DEBUG:
                self.twitter = TwitterAPI(screen_name, ct0, auth_token)
            else:
                self.twitter = None

            logger.info("----------")
            self.timeline_crawl(screen_name)
            logger.info("-----")
            self.likes_crawl(screen_name)
            logger.info("----------")
        logger.info("TimelineCrawler run -> done")


if __name__ == "__main__":
    logging.config.fileConfig("./log/logging.ini", disable_existing_loggers=False)
    for name in logging.root.manager.loggerDict:
        if "personaltwilog" in name:
            continue
        if "__main__" in name:
            continue
        getLogger(name).disabled = True

    crawler = TimelineCrawler()
    crawler.run()
