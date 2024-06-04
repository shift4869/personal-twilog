from dataclasses import dataclass


@dataclass(frozen=True)
class UserName:
    """ユーザネーム

    Args:
        _name (str): ユーザネーム
    """

    _name: str

    def __post_init__(self) -> None:
        if not isinstance(self._name, str):
            raise TypeError("name must be string.")

    @property
    def name(self) -> str:
        return self._name


if __name__ == "__main__":
    user_id = UserName("dummy_username")
    print(user_id.name)
