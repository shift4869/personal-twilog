# coding: utf-8
import json
import pprint
from dataclasses import dataclass
from pathlib import Path

import requests.cookies


@dataclass(frozen=True)
class Cookies():
    """Twitterセッションで使うクッキー
    """
    _cookies: requests.cookies.RequestsCookieJar

    # クッキーファイルパス
    TWITTER_COOKIE_PATH = "./config/twitter_cookie.json"
    # クッキーに含まれるキー一覧
    COOKIE_KEYS_LIST = ["name", "value", "expires", "path", "domain", "httponly", "secure"]

    def __post_init__(self) -> None:
        if not self._cookies:
            raise ValueError("Cookies is None.")
        if not isinstance(self._cookies, requests.cookies.RequestsCookieJar):
            raise TypeError("cookies is not RequestsCookieJar, invalid Cookies.")
        if not self._is_valid_cookies():
            raise ValueError("Cookies is invalid.")

    def _is_valid_cookies(self) -> bool:
        cookies_dict_list = self.requests_cookie_jar_to_dict(self._cookies).get("cookies", [])
        for cookies_dict in cookies_dict_list:
            match cookies_dict:
                case {
                    "name": name,
                    "value": value,
                    "expires": expires,
                    "path": path,
                    "domain": domain,
                    "secure": secure,
                    "httponly": httponly,
                }:
                    pass
                case _:
                    return False
        return True

    @property
    def cookies(self) -> requests.cookies.RequestsCookieJar:
        return self._cookies

    @classmethod
    def cookies_list_to_requests_cookie_jar(cls, cookies_list: list[dict]) -> requests.cookies.RequestsCookieJar:
        if cookies_list == []:
            raise ValueError("cookies_list is empty.")
        if not isinstance(cookies_list, list):
            raise TypeError("cookies_list is not list.")
        if not isinstance(cookies_list[0], dict):
            raise TypeError("cookies_list is not list[dict].")

        result_cookies = requests.cookies.RequestsCookieJar()
        for c in cookies_list:
            match c:
                case {
                    "name": name,
                    "value": value,
                    "expires": expires,
                    "path": path,
                    "domain": domain,
                    "secure": secure,
                    "httpOnly": httponly,
                }:
                    result_cookies.set(
                        name,
                        value,
                        expires=expires,
                        path=path,
                        domain=domain,
                        secure=secure,
                        rest={"HttpOnly": httponly}
                    )
                case _:
                    raise ValueError("cookie is not acceptable dict.")
        return result_cookies

    @classmethod
    def load(cls) -> requests.cookies.RequestsCookieJar:
        # アクセスに使用するクッキーファイル置き場
        scp = Path(Cookies.TWITTER_COOKIE_PATH)
        if not scp.exists():
            # クッキーファイルが存在しない = 初回起動
            raise FileNotFoundError

        # クッキーを読み込む
        cookies = requests.cookies.RequestsCookieJar()
        with scp.open(mode="r") as fin:
            sc_json: dict = json.load(fin)
            sc_list: list[dict] = sc_json.get("cookies", [])
            for sc in sc_list:
                cookies.set(
                    sc["name"],
                    sc["value"],
                    expires=sc["expires"],
                    path=sc["path"],
                    domain=sc["domain"],
                    secure=bool(sc["secure"]),
                    rest={"HttpOnly": bool(sc["httponly"])}
                )
        return cookies

    @classmethod
    def requests_cookie_jar_to_dict(cls, cookies: requests.cookies.RequestsCookieJar) -> dict:
        cookies_dict_list = []
        for c in cookies:
            cookies_dict = {
                "name": c.name,
                "value": c.value,
                "expires": c.expires,
                "path": c.path,
                "domain": c.domain,
                "secure": c.secure,
                "httponly": c._rest.get("HttpOnly", False),
            }
            cookies_dict_list.append(cookies_dict)
        result_dict = {
            "cookies": cookies_dict_list
        }
        return result_dict

    @classmethod
    def save(cls, cookies: requests.cookies.RequestsCookieJar | list[dict]) -> requests.cookies.RequestsCookieJar:
        if cookies and isinstance(cookies, list) and isinstance(cookies[0], dict):
            cookies = cls.cookies_list_to_requests_cookie_jar(cookies)

        if not isinstance(cookies, requests.cookies.RequestsCookieJar):
            raise TypeError("cookies is not RequestsCookieJar | list[dict].")

        # クッキー情報をファイルに保存する
        scp = Path(Cookies.TWITTER_COOKIE_PATH)
        with scp.open(mode="w") as fout:
            cookies_dict = cls.requests_cookie_jar_to_dict(cookies)
            json.dump(cookies_dict, fout, indent=4)
        return cookies

    @classmethod
    def create(cls) -> "Cookies":
        return cls(cls.load())


if __name__ == "__main__":
    try:
        cookies = Cookies.create()
        Cookies.save(cookies.cookies)
        for cookie in cookies.cookies:
            pprint.pprint(cookie)
    except Exception as e:
        pprint.pprint(e)
