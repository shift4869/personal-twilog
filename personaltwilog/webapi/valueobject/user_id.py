# coding: utf-8
from dataclasses import dataclass


@dataclass(frozen=True)
class UserId():
    """ユーザID

    Args:
        _id (int): ユーザID

    Attributes:
        id_str (str): ユーザIDを文字列に変換したもの
    """
    _id: int

    def __post_init__(self) -> None:
        if not isinstance(self._id, int):
            raise TypeError("id must be integer.")
        if self._id < 0:
            raise ValueError("id must be 0 or greater.")

    @property
    def id(self) -> int:
        return self._id

    @property
    def id_str(self) -> str:
        return str(self._id)


if __name__ == "__main__":
    user_id = UserId(123)
    print(user_id.id)
    print(user_id.id_str)
