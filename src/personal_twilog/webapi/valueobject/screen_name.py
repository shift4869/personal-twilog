import re
from dataclasses import dataclass


@dataclass(frozen=True)
class ScreenName:
    """スクリーンネーム

    半角英数とアンダーバーのみで構成される

    Args:
        _name (str): スクリーンネーム

    Attributes:
        PATTERN (str): スクリーンネームとして許容されるパターン
    """

    _name: str

    PATTERN = "^[0-9a-zA-Z_]+$"

    def __post_init__(self) -> None:
        if not isinstance(self._name, str):
            raise TypeError("name must be str.")
        if not re.search(self.PATTERN, self._name):
            raise ValueError(f"name must be pattern of '{self.PATTERN}'.")

    @property
    def name(self) -> str:
        return self._name


if __name__ == "__main__":
    screen_name = ScreenName("screen_name_1")
    print(screen_name.name)

    try:
        screen_name = ScreenName("不正なスクリーンネーム")
    except ValueError as e:
        print(e)
