import logging.config
from logging import INFO, getLogger

from personal_twilog.timeline_crawler import TimelineCrawler

logging.config.fileConfig("./log/logging.ini", disable_existing_loggers=False)
for name in logging.root.manager.loggerDict:
    if "personal_twilog" not in name:
        getLogger(name).disabled = True
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
