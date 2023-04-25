# coding: utf-8
from dataclasses import dataclass


@dataclass(frozen=True)
class UserName():
    """ユーザ名

    Args:
        _name (str): ユーザ名
    """
    _name: str

    def __post_init__(self) -> None:
        if not isinstance(self._name, str):
            raise TypeError("name must be str.")

    @property
    def name(self) -> str:
        return self._name


if __name__ == "__main__":
    user_name = UserName("ユーザー1")
    print(user_name.name)
