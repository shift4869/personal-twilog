from enum import Enum, auto
from functools import reduce
from typing import Any


class Result(Enum):
    success = auto()
    failed = auto()


def find_value(target_dict: dict, key_path: tuple[str], default: Any = "") -> Any:
    """辞書をキーのパスで探索して値を取り出す

    functools.reduce は 2値を受け取る関数, イテラブル, 初期値 を受け取る高階関数である
    たとえば reduce(lambda x, y: x+y, [1, 2, 3, 4, 5], 10) = 25 となる
    初期値に辞書、2値関数に辞書から値を取り出す関数（実質__getitem__）、
    イテラブルにキーのリストを渡すと、繰り返し適用されて辞書を掘ることができる
    たとえば t = {"a":{"b":{"c":{"d":{"e": "value"}}}}} のとき
    reduce(lambda v, k: v[k], ("a", "b", "c", "d", "e") , t) = "value" となる

    Args:
        target_dict (dict): 探索対象の辞書
        key_path (tuple[str]): キーのパス
        default (Any): 探索失敗時に返すデフォルト値

    Returns:
        Any: 辞書の値, 見つからなかった場合 default を返す
    """
    return reduce(lambda v, k: v.get(k, default) if isinstance(v, dict) else default, key_path, target_dict)


def find_values(
    obj: Any,
    key: str,
    is_predict_one: bool = False,
    key_white_list: list[str] = None,
    key_black_list: list[str] = None,
) -> list:
    if not key_white_list:
        key_white_list = []
    if not key_black_list:
        key_black_list = []

    def _inner_helper(inner_obj: Any, inner_key: str, inner_result: list) -> list:
        if isinstance(inner_obj, dict) and (inner_dict := inner_obj):
            for k, v in inner_dict.items():
                if k == inner_key:
                    inner_result.append(v)
                if key_white_list and (k not in key_white_list):
                    continue
                if k in key_black_list:
                    continue
                inner_result.extend(_inner_helper(v, inner_key, []))
        if isinstance(inner_obj, list) and (inner_list := inner_obj):
            for element in inner_list:
                inner_result.extend(_inner_helper(element, inner_key, []))
        return inner_result

    result = _inner_helper(obj, key, [])
    if not is_predict_one:
        return result

    if len(result) < 1:
        raise ValueError(f"Value of key='{key}' is not found.")
    if len(result) > 1:
        raise ValueError(f"Value of key='{key}' are multiple found.")
    return result[0]


def remove_duplicates(dict_list: list[dict]) -> list[dict]:
    """辞書リストから重複を削除する

    リストの要素について、 DUP_TARGET_KEY をキーとして、その値が重複している要素を排除する

    Args:
        dict_list (list[dict]): 対象辞書リスト

    Raises:
        ValueError: 引数の型が不正、または DUP_TARGET_KEY をキーとする要素の辞書のリストではなかった

    Returns:
        list[dict]: 重複を排除した辞書リスト
    """
    if not isinstance(dict_list, list):
        raise ValueError("Argument dict_list is not list.")
    if not all([isinstance(d, dict) for d in dict_list]):
        raise ValueError("Argument dict_list is not list[dict].")

    DUP_TARGET_KEY = "tweet_id"
    key_check = [d.get(DUP_TARGET_KEY, "") != "" for d in dict_list]
    if not all(key_check):
        raise ValueError(f"Argument dict_list include element that not has '{DUP_TARGET_KEY}' key.")

    seen = []
    dict_list = [
        d
        for d in dict_list
        if (tweet_id := d.get(DUP_TARGET_KEY, "")) != "" and (tweet_id not in seen) and (not seen.append(tweet_id))
    ]
    return dict_list
