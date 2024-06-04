import re
from datetime import datetime, timedelta
from pathlib import Path
from typing import Self

import orjson
from sqlalchemy import Column, Integer, String, create_engine, text
from sqlalchemy.orm import declarative_base, sessionmaker
from tqdm import tqdm

from personal_twilog.util import Result, find_values

Base = declarative_base()
date_str = datetime.now().strftime("%Y%m%d")
table_name = f"TweetArchive_{date_str}"


class ArchivedTweet(Base):
    __tablename__ = table_name

    id = Column(Integer, primary_key=True)
    tweet_id = Column(String)
    tweet_text = Column(String)
    tweet_via = Column(String)
    tweet_url = Column(String)
    user_id = Column(String)
    user_name = Column(String)
    screen_name = Column(String)
    is_retweet = Column(String)
    retweet_tweet_id = Column(String)
    is_quote = Column(String)
    quote_tweet_id = Column(String)
    has_media = Column(String)
    has_external_link = Column(String)
    created_at = Column(String)
    appeared_at = Column(String)
    registered_at = Column(String)

    def __init__(
        self,
        tweet_id,
        tweet_text,
        tweet_via,
        tweet_url,
        user_id,
        user_name,
        screen_name,
        is_retweet,
        retweet_tweet_id,
        is_quote,
        quote_tweet_id,
        has_media,
        has_external_link,
        created_at,
        appeared_at,
        registered_at,
    ):
        self.tweet_id = tweet_id
        self.tweet_text = tweet_text
        self.tweet_via = tweet_via
        self.tweet_url = tweet_url
        self.user_id = user_id
        self.user_name = user_name
        self.screen_name = screen_name
        self.is_retweet = is_retweet
        self.retweet_tweet_id = retweet_tweet_id
        self.is_quote = is_quote
        self.quote_tweet_id = quote_tweet_id
        self.has_media = has_media
        self.has_external_link = has_external_link
        self.created_at = created_at
        self.appeared_at = appeared_at
        self.registered_at = registered_at

    @classmethod
    def create(cls, entry: dict) -> Self:
        tweet_dict = find_values(entry, "tweet", True, [""], [])
        tweet_id = find_values(tweet_dict, "id_str", True, [""], [])
        tweet_text = find_values(tweet_dict, "full_text", True, [""], [])

        source = find_values(tweet_dict, "source", True, [""], [])
        tweet_via = re.findall(r"<[^>]+>(.*?)<\/[^<]+>", source)[0]

        user_id = "175674367"
        user_name = "shift@ヽ(・ω・)ノ"
        screen_name = "_shift4869"

        tweet_url = f"https://twitter.com/{screen_name}/status/{tweet_id}"

        src_format = "%a %b %d %H:%M:%S %z %Y"
        created_at_str = find_values(tweet_dict, "created_at", True, [""], [])
        gmt = datetime.strptime(created_at_str, src_format)
        jst = gmt + timedelta(hours=9)
        created_at = jst.isoformat().replace("+00:00", "")
        appeared_at = created_at
        registered_at = datetime.now().isoformat()[:-7]

        # RT の構造解析は厳密には行わない
        is_retweet = re.findall(r"^RT @(.*)", tweet_text) != []
        source_status_ids = find_values(tweet_dict, "source_status_id_str", False, [], [])
        retweet_tweet_id = source_status_ids[0] if len(source_status_ids) > 0 and is_retweet else ""

        expanded_urls = find_values(tweet_dict, "expanded_url", False, [], [])
        contain_twitter_url_flag = [
            (re.findall(r"^https://twitter.com/(.*)/status/(\d*)$", url) != []) for url in expanded_urls
        ]
        is_quote = any(contain_twitter_url_flag)
        quote_tweet_id = ""
        if is_quote:
            for url in expanded_urls:
                if m := re.findall(r"^https://twitter.com/(.*)/status/(\d*)$", url):
                    quote_tweet_id = m[0][1]

        media = find_values(tweet_dict, "media", False, [], [])
        has_media = media != []

        entities = find_values(tweet_dict, "entities", False, [], [])
        external_link = find_values(entities, "expanded_url", False, [], [])
        has_external_link = external_link != []

        return ArchivedTweet(
            tweet_id,
            tweet_text,
            tweet_via,
            tweet_url,
            user_id,
            user_name,
            screen_name,
            is_retweet,
            retweet_tweet_id,
            is_quote,
            quote_tweet_id,
            has_media,
            has_external_link,
            created_at,
            appeared_at,
            registered_at,
        )


def main(input_base_path: Path, output_db_path: Path) -> Result:
    """PersonalTwilog 用にアーカイブからロードする

    Args:
        input_base_path (Path): 入力アーカイブのベースパス
        output_db_path (Path): 結果反映先のDBパス
    """

    # DB生成
    engine = create_engine(f"sqlite:///{output_db_path}")
    Base.metadata.create_all(engine)

    # セッション生成
    Session = sessionmaker(bind=engine)
    session = Session()

    # Truncate
    truncate_query = f"DELETE FROM {table_name}"
    session.execute(text(truncate_query))
    session.commit()

    # json ファイル読み込み
    json_dir = input_base_path / "data"
    json_path_list = [json_dir / "tweets.js"]
    json_path_list.extend(json_dir.glob("tweets-part*"))
    tweet_list: list[ArchivedTweet] = []
    for i, json_path in enumerate(json_path_list):
        all_str = json_path.read_text("utf8")
        all_str = all_str.replace(f"window.YTD.tweets.part{i} = ", "")
        json_dict = orjson.loads(all_str.encode())
        for entry in tqdm(json_dict, desc=f"{json_path.name}"):
            t = ArchivedTweet.create(entry)
            tweet_list.append(t)

    # created_at で昇順ソート
    tweet_list.sort(key=lambda t: t.created_at)

    # DB Insert
    for tweet in tqdm(tweet_list, desc=f"DB Insert"):
        session.add(tweet)
    print("DB commiting ...")
    session.commit()
    session.close()
    print("DB commit done.")
    return Result.SUCCESS


if __name__ == "__main__":
    input_base_path = Path("I:/Users/shift/Documents/twitter_backup/twitter-2023-09-22")
    output_db_path = Path("D:/Users/shift/Documents/git/personal-twilog/timeline.db")
    main(input_base_path, output_db_path)
