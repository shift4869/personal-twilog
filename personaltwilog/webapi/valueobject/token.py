from dataclasses import dataclass
from typing import Self

from personaltwilog.webapi.valueobject.screen_name import ScreenName


@dataclass(frozen=True)
class Token:
    """twitter-api-client の認証に使うトークン情報

    Attributes:
        screen_name (ScreenName): トークンに紐づくスクリーンネーム
        ct0 (str): トークン情報ct0
        auth_token (str):  トークン情報auth_token
    """

    screen_name: ScreenName
    ct0: str
    auth_token: str

    def __post_init__(self) -> None:
        if not isinstance(self.screen_name, ScreenName):
            raise TypeError("screen_name must be ScreenName.")
        if not isinstance(self.ct0, str):
            raise TypeError("ct0 must be str.")
        if not isinstance(self.auth_token, str):
            raise TypeError("auth_token must be str.")

    @classmethod
    def create(cls, screen_name: ScreenName | str, ct0: str, auth_token: str) -> Self:
        if isinstance(screen_name, str):
            screen_name = ScreenName(screen_name)
        return Token(screen_name, ct0, auth_token)


if __name__ == "__main__":
    token = Token.create("dummy_screen_name", "dummy_ct0", "dummy_auth_token")
    print(token.screen_name.name)
