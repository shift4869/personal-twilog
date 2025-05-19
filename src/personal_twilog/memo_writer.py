import logging.config
import re
import shutil
from datetime import datetime
from enum import Enum, auto
from logging import INFO, getLogger
from pathlib import Path

import orjson
from dateutil.relativedelta import relativedelta

from personal_twilog.util import Result

logger = getLogger(__name__)
logger.setLevel(INFO)


class MemoWriter:
    INSERT_TARGET_MARKER = "#### メモ\n\n"

    def __init__(self) -> None:
        logger.info("MemoWriter init -> start")
        CONFIG_FILE_NAME = "./config/config.json"
        config = orjson.loads(Path(CONFIG_FILE_NAME).read_bytes())

        self.config = config["memo_writer"]

        self.vault_base_path: Path = Path(self.config["vault_base_path"])
        self.now_date: datetime = datetime.now()
        self.now_date_str: str = self.now_date.strftime("%Y-%m-%d")
        self.year_month: str = self.now_date.strftime("%Y%m")
        self.dst_path: Path = self.vault_base_path / "diary" / self.year_month / f"{self.now_date_str}.md"
        self.is_enable: bool = self.config["status"] == "enable" and self.dst_path.exists()
        logger.info("MemoWriter init -> done")

    def write(self, memo: str) -> Result:
        logger.info("MemoWriter write -> start")
        if not self.is_enable:
            return Result.failed
        # 既存テキストをすべて読み込む
        content = self.dst_path.read_text(encoding="utf-8")

        # マーカーから次の空行までの文字列を取得する
        pattern = f".*{self.INSERT_TARGET_MARKER}(.*?)\n.*"
        exist_sentence = re.search(pattern, content)
        if not exist_sentence:
            return Result.failed
        exist_sentence = exist_sentence[0].replace(self.INSERT_TARGET_MARKER, "")

        # 取得文字列が末尾が\nでないなら補完
        if not exist_sentence.endswith("\n"):
            exist_sentence = exist_sentence + "\n"
        # 末尾がmemoそのものなら二重登録と判断して置き換えをしない
        if exist_sentence.endswith(f"{memo}\n"):
            return Result.success

        # 置き換え後の文字列を生成
        updated_sentence = f"{exist_sentence}{memo}\n" if exist_sentence != "\n" else f"{memo}\n"
        # 置き換え後のテキスト全体を生成
        updated_content = content.replace(
            self.INSERT_TARGET_MARKER + exist_sentence, self.INSERT_TARGET_MARKER + updated_sentence, 1
        )

        # 置き換え後のテキストを書き込む
        self.dst_path.write_text(updated_content, encoding="utf-8")
        logger.info("MemoWriter write -> done")
        return Result.success

    def search(self, tweet_dict_list: list[dict]) -> Result:
        logger.info("MemoWriter search -> start")
        if not self.is_enable:
            return Result.failed
        for tweet_dict in tweet_dict_list:
            tweet_text: str = tweet_dict["tweet_text"]
            if tweet_text.startswith("メモ："):
                self.write(tweet_text[3:])
        logger.info("MemoWriter search -> done")
        return Result.success

    def search_and_write(self, tweet_dict_list: list[dict]) -> Result:
        logger.info("MemoWriter search_and_write -> start")
        if not self.is_enable:
            logger.info("Memo is not included.")
            logger.info("MemoWriter search_and_write -> done")
            return Result.success
        self.search(tweet_dict_list)
        logger.info("MemoWriter search_and_write -> done")
        return Result.success


if __name__ == "__main__":
    logging.config.fileConfig("./log/logging.ini", disable_existing_loggers=False)
    for name in logging.root.manager.loggerDict:
        if "personaltwilog" in name:
            continue
        if "__main__" in name:
            continue
        getLogger(name).disabled = True

    memo_writer = MemoWriter()
    memo_writer.write("test")
