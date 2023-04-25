# coding: utf-8
import json
import pprint
import re
from dataclasses import dataclass
from enum import Enum, auto
from pathlib import Path


class TwitterAPIEndpointName(Enum):
    """エンドポイント名一覧
    
        指定のエンドポイントurlを取得したい場合は以下のように使用する
            url = TwitterAPIEndpoint.make_url(TwitterAPIEndpointName.USER_LOOKUP_ME)
        TwitterAPIEndpoint.SETTING_JSON_PATH で示されるjsonファイル内の
        endpoint[].name に対応する
    """
    TIMELINE_TWEET = auto()  # ツイート取得(userid)
    POST_TWEET = auto()  # ツイート投稿
    DELETE_TWEET = auto()  # ツイート削除(tweetid)
    USER_LOOKUP = auto()  # ユーザー詳細取得
    USER_LOOKUP_BY_USERNAME = auto()  # ユーザー詳細取得(screen_name)
    TWEETS_LOOKUP = auto()  # ツイート詳細取得
    LIKED_TWEET = auto()  # like 取得(userid)
    USER_LOOKUP_ME = auto()  # 認証ユーザー詳細取得
    FOLLOWING = auto()  # Following 取得(userid)
    FOLLOWER = auto()  # Follower 取得(userid)
    GET_MEMBER_FROM_LIST = auto()  # リストメンバー取得(listid)
    ADD_MEMBER_TO_LIST = auto()  # リストメンバー追加(listid)
    GET_MUTE_KEYWORD_LIST = auto()  # ミュートキーワードリストを取得
    POST_MUTE_KEYWORD = auto()  # キーワードをミュートする
    POST_UNMUTE_KEYWORD = auto()  # キーワードのミュートを解除する
    POST_MUTE_USER = auto()  # ユーザーをミュートする
    POST_UNMUTE_USER = auto()  # ユーザーのミュートを解除する
    # レートリミット(未実装)


@dataclass
class TwitterAPIEndpoint():
    """エンドポイントに関わる情報を管理するクラス

        TwitterAPIEndpoint.SETTING_JSON_PATH にあるjsonファイルを参照する
        インスタンスは作らず、クラスメソッドのみで機能を使用する
        self.setting_dict はシングルトン
    """
    # 設定ファイルパス
    SETTING_JSON_PATH = "./config/twitter_webapi_setting.json"
    setting_dict = {}

    @classmethod
    def _is_json_endpoint_struct_match(cls, estimated_endpoint_dict: dict) -> bool:
        """指定辞書の endpoint 構造部分について判定する

        Args:
            estimated_endpoint_dict (dict): endpoint 構造をしていると思われる辞書(単体)

        Returns:
            bool: endpoint 構造が正しいならばTrue, 不正ならばFalse
        """
        match estimated_endpoint_dict:
            case {"name": name,
                  "method": method,
                  "path_params_num": path_params_num,
                  "template": template,
                  "url": url}:
                if not isinstance(name, str):
                    return False
                if not isinstance(method, str):
                    return False
                if not isinstance(path_params_num, int):
                    return False
                if not isinstance(template, str):
                    return False
                if not isinstance(url, str):
                    return False
                return True
        return False

    @classmethod
    def _raise_for_json_struct_match(cls, estimated_setting_dict: dict) -> None:
        """指定辞書の構造が正しいか判定する

        Args:
            estimated_setting_dict (dict): 対象の辞書

        Raises:
            ValueError: 辞書構造が不正な場合
        """
        if not isinstance(estimated_setting_dict, dict):
            raise ValueError("setting_dict must be dict.")
        if "endpoint" not in estimated_setting_dict:
            raise ValueError('invalid setting_dict, must have "endpoint".')

        endpoint_list = estimated_setting_dict.get("endpoint", [])
        if not endpoint_list:
            raise ValueError('invalid setting_dict, must have "endpoint".')
        valid_endpoint_struct = [cls._is_json_endpoint_struct_match(endpoint) for endpoint in endpoint_list]
        if not all(valid_endpoint_struct):
            raise ValueError('invalid setting_dict, must have valid "endpoint" struct.')
        return

    @classmethod
    def load(cls) -> None:
        """jsonファイルをロードして cls.setting_dict を使用可能にする

            設定jsonファイルは cls.SETTING_JSON_PATH
            ロード後の cls.setting_dict の構造もチェックする
        """
        with Path(cls.SETTING_JSON_PATH).open("r") as fin:
            cls.setting_dict = json.loads(fin.read())
        cls._raise_for_json_struct_match(cls.setting_dict)

    @classmethod
    def reload(cls) -> None:
        """リロード
        """
        cls.load()

    @classmethod
    def save(cls, new_endpoint_dict) -> None:
        """保存
        """
        cls._raise_for_json_struct_match(new_endpoint_dict)
        with Path(cls.SETTING_JSON_PATH).open("w") as fout:
            json.dump(new_endpoint_dict, fout, indent=4)
        cls.reload()

    @classmethod
    def get_setting_dict(cls) -> dict:
        """cls.setting_dict を返す

            初回呼び出し時は load する（シングルトン）
            2回目以降は保持している cls.setting_dict をそのまま返す

        Returns:
            dict: cls.setting_dict
        """
        if not cls.setting_dict:
            cls.load()
            return cls.setting_dict
        else:
            return cls.setting_dict

    @classmethod
    def _get(cls, key: str) -> list[dict]:
        """指定 key を持つ辞書の一部を返す

        Args:
            key (str): 探索対象のキー

        Returns:
            list[dict]: 見つかった辞書（単体でもリストとして返す）
        """
        if not isinstance(key, str):
            raise ValueError("key must be str.")
        setting_dict: dict = cls.get_setting_dict()
        res = setting_dict.get(key)
        if not isinstance(res, list):
            res = [res]
        return res

    @classmethod
    def get_endpoint_list(cls) -> list[dict]:
        """cls.setting_dict["endpoint"] を返す

        Returns:
            list[dict]: cls.setting_dict["endpoint"]
        """
        return cls._get("endpoint")

    @classmethod
    def get_endpoint(cls, name: TwitterAPIEndpointName) -> dict:
        """指定 name を持つ cls.setting_dict["endpoint"] の要素を返す

        Args:
            name (TwitterAPIEndpointName): 探索対象の name

        Returns:
            dict: cls.setting_dict["endpoint"] の要素のうち、"name" が引数と一致する要素
                  見つからなかった場合は空辞書を返す
        """
        if not isinstance(name, TwitterAPIEndpointName):
            raise ValueError("name must be TwitterAPIEndpointName.")
        endpoint_list = cls.get_endpoint_list()
        res = [endpoint for endpoint in endpoint_list if endpoint.get("name", "") == name.name]
        if not res:
            return {}
        return res[0]

    @classmethod
    def make_url(cls, name: TwitterAPIEndpointName, *args) -> str:
        """指定 name からエンドポイントURLを返す

        Args:
            name (TwitterAPIEndpointName): 探索対象の name

        Returns:
            str: 指定の name に紐づくエンドポイントURL
        """
        if not isinstance(name, TwitterAPIEndpointName):
            raise ValueError("name must be TwitterAPIEndpointName.")
        endpoint = cls.get_endpoint(name)

        path_params_num = int(endpoint.get("path_params_num", 0))
        url = endpoint.get("url", "")

        if path_params_num > 0:
            if path_params_num != len(args):
                raise ValueError(f"*args len must be {path_params_num}, len(args) = {len(args)}.")
            url = url.format(*args)
        return url


if __name__ == "__main__":
    # 存在するAPIエンドポイントをすべて表示
    for name in TwitterAPIEndpointName:
        pprint.pprint(f"{name.name}")
    # TwitterAPIEndpoint.load()
    # pprint.pprint(TwitterAPIEndpoint.setting_dict)
    url = TwitterAPIEndpoint.make_url(TwitterAPIEndpointName.GET_MUTE_KEYWORD_LIST)
    pprint.pprint(url)
