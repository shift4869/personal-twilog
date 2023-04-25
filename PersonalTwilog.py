# coding: utf-8
import configparser
import logging.config
import sys
from logging import INFO, getLogger

from personaltwilog.TimelineCrawler import TimelineCrawler

logging.config.fileConfig("./log/logging.ini", disable_existing_loggers=False)
for name in logging.root.manager.loggerDict:
    if "personaltwilog" not in name:
        getLogger(name).disabled = True
logger = getLogger(__name__)
logger.setLevel(INFO)

if __name__ == "__main__":
    crawler = TimelineCrawler()
    crawler.run()
