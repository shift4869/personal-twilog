# coding: utf-8
import json
import pprint
from dataclasses import dataclass
from pathlib import Path
from typing import Self


@dataclass(frozen=True)
class BearerToken():
    """Twitterセッションで使う Bearer トークン
    """
    _token_dict: dict

    # Bearer トークンファイルパス
    TWITTER_BEARER_TOKEN_PATH = "./config/twitter_bearer_token.json"

    def __post_init__(self) -> None:
        if not self._token_dict:
            raise ValueError("Bearer token is None.")
        if not isinstance(self._token_dict, dict):
            raise TypeError("Bearer token is not dict, invalid Bearer token.")
        if not self.is_valid(self._token_dict):
            raise ValueError("Bearer token is invalid.")
        if not self.bearer_token.startswith("Bearer "):
            raise ValueError("Bearer token is not start with 'Bearer '.")

    @classmethod
    def is_valid(cls, bearer_token_dict: dict) -> bool:
        match bearer_token_dict:
            case {
                "origin": _,
                "x-twitter-client-language": _,
                "x-csrf-token": _,
                "authorization": bearer_token,
                "content-type": _,
                "user-agent": _,
                "referer": _,
                "x-twitter-auth-type": _,
                "x-twitter-active-user": _
            }:
                if not bearer_token:
                    return False
                if not isinstance(bearer_token, str):
                    return False
                if not bearer_token.startswith("Bearer "):
                    return False
                return True
            case _:
                return False

    def to_dict(self) -> dict:
        return self._token_dict

    @property
    def bearer_token(self) -> str:
        bearer_token = self._token_dict.get("authorization", "")
        if not bearer_token:
            raise ValueError("Bearer token is None, token_dict is not included 'authorization' key-value.")
        if not isinstance(bearer_token, str):
            raise ValueError("Bearer token is not str")
        if not bearer_token.startswith("Bearer "):
            raise ValueError("Bearer token is not start with 'Bearer '.")
        return bearer_token

    @classmethod
    def load(cls) -> dict:
        bcp = Path(BearerToken.TWITTER_BEARER_TOKEN_PATH)
        if not bcp.exists():
            raise FileNotFoundError

        result = {}
        with bcp.open(mode="r") as fin:
            result: dict = json.load(fin)
        return result

    @classmethod
    def save(cls, bearer_token_dict: dict) -> dict:
        if not isinstance(bearer_token_dict, dict):
            raise TypeError("bearer_token_dict is not dict.")
        if not cls.is_valid(bearer_token_dict):
            raise TypeError("bearer_token_dict is not acceptable dict.")

        bcp = Path(BearerToken.TWITTER_BEARER_TOKEN_PATH)
        with bcp.open(mode="w") as fout:
            json.dump(bearer_token_dict, fout, indent=4)
        return bearer_token_dict

    @classmethod
    def create(cls) -> Self:
        return cls(cls.load())


if __name__ == "__main__":
    try:
        bearer_token = BearerToken.create()
        BearerToken.save(bearer_token.to_dict())
        pprint.pprint(bearer_token)
    except Exception as e:
        pprint.pprint(e)
