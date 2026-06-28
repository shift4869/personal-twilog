import logging.config
from logging import INFO, getLogger

from personal_twilog.timeline_crawler import TimelineCrawler
from personal_twilog.util import log_suppress

logging.config.fileConfig("./log/logging.ini", disable_existing_loggers=False)
log_suppress()
logger = getLogger(__name__)
logger.setLevel(INFO)

if __name__ == "__main__":
    HORIZONTAL_LINE = "-" * 80
    logger.info(HORIZONTAL_LINE)
    try:
        crawler = TimelineCrawler()
        crawler.run()
    except Exception as e:
        logger.exception(e)
    logger.info(HORIZONTAL_LINE)
