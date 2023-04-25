# coding: utf-8
import json
import pprint
import re
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class LocalStorage():
    """Twitterセッションで使うローカルストレージ
    """
    _local_storage: dict

    # ローカルストレージファイルパス
    TWITTER_LOCAL_STORAGE_PATH = "./config/twitter_localstorage.json"

    def __post_init__(self) -> None:
        # _local_storage = {} は許容する
        if (not self._local_storage) and (self._local_storage != {}):
            raise ValueError("LocalStorage is None.")
        if not isinstance(self._local_storage, dict):
            raise TypeError("LocalStorage is not dict, invalid LocalStorage.")
        if not self._is_valid_local_storage():
            raise ValueError("LocalStorage is invalid.")

    def _is_valid_local_storage(self) -> bool:
        local_storage = self._local_storage
        # TODO::local_storage が満たすべき条件を記述
        return True

    @property
    def local_storage(self) -> dict:
        return self._local_storage

    @classmethod
    def validate_line(cls, line) -> bool:
        pattern = "^(.*?) : (.*)$"
        if re.findall(pattern, line):
            return True
        return False

    @classmethod
    def dict_to_line(cls, line_dict: dict) -> list[str]:
        result = []
        for key, value in line_dict.items():
            result.append(f"{key} : {value}")
        return result

    @classmethod
    def load(cls) -> dict:
        # アクセスに使用するローカルストレージファイル置き場
        slsp = Path(LocalStorage.TWITTER_LOCAL_STORAGE_PATH)
        if not slsp.exists():
            # ローカルストレージファイルが存在しない = 初回起動
            raise FileNotFoundError

        # ローカルストレージを読み込む
        local_storage_dict: dict = {}
        with slsp.open(mode="r") as fin:
            local_storage_dict = json.load(fin)
        local_storage = local_storage_dict.get("local_storage", [])
        return local_storage

    @classmethod
    def save(cls, local_storage: list[str]) -> list[str]:
        # _local_storage = [] は許容する
        if not isinstance(local_storage, list):
            raise TypeError("local_storage is not list.")

        # ローカルストレージ情報を保存
        slsp = Path(cls.TWITTER_LOCAL_STORAGE_PATH)
        local_storage_dict = {}
        pattern = "^(.*?) : (.*)$"
        for line in local_storage:
            if cls.validate_line(line):
                key, value = re.findall(pattern, line)[0]
                local_storage_dict[key] = value
            else:
                raise ValueError("local_storage format error.")
        result_dict = {
            "local_storage": local_storage_dict
        }
        with slsp.open("w") as fout:
            json.dump(result_dict, fout, indent=4)

        return local_storage

    @classmethod
    def create(cls) -> "LocalStorage":
        return cls(cls.load())


if __name__ == "__main__":
    try:
        ls = LocalStorage.create()
        local_storage_line_list = LocalStorage.dict_to_line(ls.local_storage)
        LocalStorage.save(local_storage_line_list)
        pprint.pprint(ls)
    except Exception as e:
        pprint.pprint(e)
