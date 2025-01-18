from datetime import datetime
from pathlib import Path
from typing import Self

from sqlalchemy import Boolean, Column, Integer, Numeric, String, create_engine
from sqlalchemy.orm import Session, declarative_base

Base = declarative_base()


class Tweet(Base):
    """ツイートモデル
    [id] INTEGER NOT NULL UNIQUE,
    [tweet_id] TEXT NOT NULL,
    [tweet_text] TEXT,
    [tweet_via] TEXT,
    [tweet_url] TEXT NOT NULL,
    [user_id] TEXT NOT NULL,
    [user_name] TEXT NOT NULL,
    [screen_name] TEXT NOT NULL,
    [is_retweet] Boolean,
    [retweet_tweet_id] TEXT,
    [is_quote] Boolean,
    [quote_tweet_id] TEXT,
    [has_media] Boolean,
    [has_external_link] Boolean,
    [created_at] TEXT NOT NULL,
    [appeared_at] TEXT NOT NULL,
    [registered_at] TEXT NOT NULL,
    PRIMARY KEY([id])
    """

    __tablename__ = "Tweet"

    id = Column(Integer, primary_key=True)
    tweet_id = Column(String(256), nullable=False, unique=True)
    tweet_text = Column(String(256))
    tweet_via = Column(String(256))
    tweet_url = Column(String(256), nullable=False)
    user_id = Column(String(256), nullable=False)
    user_name = Column(String(256), nullable=False)
    screen_name = Column(String(256), nullable=False)
    is_retweet = Column(Boolean(), nullable=False)
    retweet_tweet_id = Column(String(256))
    is_quote = Column(Boolean(), nullable=False)
    quote_tweet_id = Column(String(256))
    has_media = Column(Boolean(), nullable=False)
    has_external_link = Column(Boolean(), nullable=False)
    created_at = Column(String(256), nullable=False)
    appeared_at = Column(String(256), nullable=False)
    registered_at = Column(String(256), nullable=False)

    def __init__(
        self,
        tweet_id: str,
        tweet_text: str,
        tweet_via: str,
        tweet_url: str,
        user_id: str,
        user_name: str,
        screen_name: str,
        is_retweet: bool,
        retweet_tweet_id: str,
        is_quote: bool,
        quote_tweet_id: str,
        has_media: bool,
        has_external_link: bool,
        created_at: str,
        appeared_at: str,
        registered_at: str,
    ):
        # self.id = id
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
    def create(self, args_dict: dict) -> Self:
        match args_dict:
            case {
                "tweet_id": tweet_id,
                "tweet_text": tweet_text,
                "tweet_via": tweet_via,
                "tweet_url": tweet_url,
                "user_id": user_id,
                "user_name": user_name,
                "screen_name": screen_name,
                "is_retweet": is_retweet,
                "retweet_tweet_id": retweet_tweet_id,
                "is_quote": is_quote,
                "quote_tweet_id": quote_tweet_id,
                "has_media": has_media,
                "has_external_link": has_external_link,
                "created_at": created_at,
                "appeared_at": appeared_at,
                "registered_at": registered_at,
            }:
                return Tweet(
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
            case _:
                raise ValueError("Unmatch args_dict.")

    def __repr__(self):
        return f"<Tweet(id='{self.tweet_id}', screen_name='{self.screen_name}')>"

    def __eq__(self, other):
        return isinstance(other, Tweet) and other.tweet_id == self.tweet_id

    def to_dict(self) -> dict:
        return {
            "tweet_id": self.tweet_id,
            "tweet_text": self.tweet_text,
            "tweet_via": self.tweet_via,
            "tweet_url": self.tweet_url,
            "user_id": self.user_id,
            "user_name": self.user_name,
            "screen_name": self.screen_name,
            "is_retweet": self.is_retweet,
            "retweet_tweet_id": self.retweet_tweet_id,
            "is_quote": self.is_quote,
            "quote_tweet_id": self.quote_tweet_id,
            "has_media": self.has_media,
            "has_external_link": self.has_external_link,
            "created_at": self.created_at,
            "appeared_at": self.appeared_at,
            "registered_at": self.registered_at,
        }


class Likes(Base):
    """Likes モデル
    [id] INTEGER NOT NULL UNIQUE,
    [tweet_id] TEXT NOT NULL,
    [tweet_text] TEXT,
    [tweet_via] TEXT,
    [tweet_url] TEXT NOT NULL,
    [tweet_user_id] TEXT NOT NULL,
    [tweet_user_name] TEXT NOT NULL,
    [tweet_screen_name] TEXT NOT NULL,
    [user_id] TEXT NOT NULL,
    [user_name] TEXT NOT NULL,
    [screen_name] TEXT NOT NULL,
    [is_retweet] Boolean,
    [retweet_tweet_id] TEXT,
    [is_quote] Boolean,
    [quote_tweet_id] TEXT,
    [has_media] Boolean,
    [has_external_link] Boolean,
    [created_at] TEXT NOT NULL,
    [appeared_at] TEXT NOT NULL,
    [registered_at] TEXT NOT NULL,
    PRIMARY KEY([id])
    """

    __tablename__ = "Likes"

    id = Column(Integer, primary_key=True)
    tweet_id = Column(String(256), nullable=False, unique=True)
    tweet_text = Column(String(256))
    tweet_via = Column(String(256))
    tweet_url = Column(String(256), nullable=False)
    tweet_user_id = Column(String(256), nullable=False)
    tweet_user_name = Column(String(256), nullable=False)
    tweet_screen_name = Column(String(256), nullable=False)
    user_id = Column(String(256), nullable=False)
    user_name = Column(String(256), nullable=False)
    screen_name = Column(String(256), nullable=False)
    is_retweet = Column(Boolean(), nullable=False)
    retweet_tweet_id = Column(String(256))
    is_quote = Column(Boolean(), nullable=False)
    quote_tweet_id = Column(String(256))
    has_media = Column(Boolean(), nullable=False)
    has_external_link = Column(Boolean(), nullable=False)
    created_at = Column(String(256), nullable=False)
    appeared_at = Column(String(256), nullable=False)
    registered_at = Column(String(256), nullable=False)

    def __init__(
        self,
        tweet_id: str,
        tweet_text: str,
        tweet_via: str,
        tweet_url: str,
        tweet_user_id: str,
        tweet_user_name: str,
        tweet_screen_name: str,
        user_id: str,
        user_name: str,
        screen_name: str,
        is_retweet: bool,
        retweet_tweet_id: str,
        is_quote: bool,
        quote_tweet_id: str,
        has_media: bool,
        has_external_link: bool,
        created_at: str,
        appeared_at: str,
        registered_at: str,
    ):
        # self.id = id
        self.tweet_id = tweet_id
        self.tweet_text = tweet_text
        self.tweet_via = tweet_via
        self.tweet_url = tweet_url
        self.tweet_user_id = tweet_user_id
        self.tweet_user_name = tweet_user_name
        self.tweet_screen_name = tweet_screen_name
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
    def create(self, args_dict: dict) -> Self:
        match args_dict:
            case {
                "tweet_id": tweet_id,
                "tweet_text": tweet_text,
                "tweet_via": tweet_via,
                "tweet_url": tweet_url,
                "tweet_user_id": tweet_user_id,
                "tweet_user_name": tweet_user_name,
                "tweet_screen_name": tweet_screen_name,
                "user_id": user_id,
                "user_name": user_name,
                "screen_name": screen_name,
                "is_retweet": is_retweet,
                "retweet_tweet_id": retweet_tweet_id,
                "is_quote": is_quote,
                "quote_tweet_id": quote_tweet_id,
                "has_media": has_media,
                "has_external_link": has_external_link,
                "created_at": created_at,
                "appeared_at": appeared_at,
                "registered_at": registered_at,
            }:
                return Likes(
                    tweet_id,
                    tweet_text,
                    tweet_via,
                    tweet_url,
                    tweet_user_id,
                    tweet_user_name,
                    tweet_screen_name,
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
            case _:
                raise ValueError("Unmatch args_dict.")

    def __repr__(self):
        return f"<Likes(id='{self.tweet_id}', screen_name='{self.screen_name}')>"

    def __eq__(self, other):
        return isinstance(other, Likes) and other.tweet_id == self.tweet_id

    def to_dict(self) -> dict:
        return {
            "tweet_id": self.tweet_id,
            "tweet_text": self.tweet_text,
            "tweet_via": self.tweet_via,
            "tweet_url": self.tweet_url,
            "tweet_user_id": self.tweet_user_id,
            "tweet_user_name": self.tweet_user_name,
            "tweet_screen_name": self.tweet_screen_name,
            "user_id": self.user_id,
            "user_name": self.user_name,
            "screen_name": self.screen_name,
            "is_retweet": self.is_retweet,
            "retweet_tweet_id": self.retweet_tweet_id,
            "is_quote": self.is_quote,
            "quote_tweet_id": self.quote_tweet_id,
            "has_media": self.has_media,
            "has_external_link": self.has_external_link,
            "created_at": self.created_at,
            "appeared_at": self.appeared_at,
            "registered_at": self.registered_at,
        }


class Media(Base):
    """メディアモデル
    [id] INTEGER NOT NULL UNIQUE,
    [tweet_id] TEXT NOT NULL,
    [tweet_text] TEXT,
    [tweet_via] TEXT,
    [tweet_url] TEXT NOT NULL,
    [media_filename] TEXT NOT NULL,
    [media_url] TEXT NOT NULL,
    [media_type] TEXT NOT NULL,
    [media_size] INTEGER NOT NULL,
    [created_at] TEXT NOT NULL,
    [appeared_at] TEXT NOT NULL,
    [registered_at] TEXT NOT NULL,
    PRIMARY KEY([id])
    """

    __tablename__ = "Media"

    id = Column(Integer, primary_key=True)
    tweet_id = Column(String(256), nullable=False, unique=True)
    tweet_text = Column(String(256))
    tweet_via = Column(String(256))
    tweet_url = Column(String(256), nullable=False)
    media_filename = Column(String(256), nullable=False)
    media_url = Column(String(256), nullable=False)
    media_thumbnail_url = Column(String(256), nullable=False)
    media_type = Column(String(256), nullable=False)
    media_size = Column(Integer, nullable=False)
    created_at = Column(String(256), nullable=False)
    appeared_at = Column(String(256), nullable=False)
    registered_at = Column(String(256), nullable=False)

    def __init__(
        self,
        tweet_id: str,
        tweet_text: str,
        tweet_via: str,
        tweet_url: str,
        media_filename: str,
        media_url: str,
        media_thumbnail_url: str,
        media_type: str,
        media_size: int,
        created_at: str,
        appeared_at: str,
        registered_at: str,
    ):
        # self.id = id
        self.tweet_id = tweet_id
        self.tweet_text = tweet_text
        self.tweet_via = tweet_via
        self.tweet_url = tweet_url
        self.media_filename = media_filename
        self.media_url = media_url
        self.media_thumbnail_url = media_thumbnail_url
        self.media_type = media_type
        self.media_size = media_size
        self.created_at = created_at
        self.appeared_at = appeared_at
        self.registered_at = registered_at

    @classmethod
    def create(self, args_dict: dict) -> Self:
        match args_dict:
            case {
                "tweet_id": tweet_id,
                "tweet_text": tweet_text,
                "tweet_via": tweet_via,
                "tweet_url": tweet_url,
                "media_filename": media_filename,
                "media_url": media_url,
                "media_thumbnail_url": media_thumbnail_url,
                "media_type": media_type,
                "media_size": media_size,
                "created_at": created_at,
                "appeared_at": appeared_at,
                "registered_at": registered_at,
            }:
                return Media(
                    tweet_id,
                    tweet_text,
                    tweet_via,
                    tweet_url,
                    media_filename,
                    media_url,
                    media_thumbnail_url,
                    media_type,
                    media_size,
                    created_at,
                    appeared_at,
                    registered_at,
                )
            case _:
                raise ValueError("Unmatch args_dict.")

    def __repr__(self):
        return f"<Media(tweet_id='{self.tweet_id}', media_filename='{self.media_filename}')>"

    def __eq__(self, other):
        return isinstance(other, Media) and other.media_url == self.media_url and other.tweet_id == self.tweet_id

    def to_dict(self) -> dict:
        return {
            "tweet_id": self.tweet_id,
            "tweet_text": self.tweet_text,
            "tweet_via": self.tweet_via,
            "tweet_url": self.tweet_url,
            "media_filename": self.media_filename,
            "media_url": self.media_url,
            "media_thumbnail_url": self.media_thumbnail_url,
            "media_type": self.media_type,
            "media_size": self.media_size,
            "created_at": self.created_at,
            "appeared_at": self.appeared_at,
            "registered_at": self.registered_at,
        }


class ExternalLink(Base):
    """外部リンクモデル
    [id] INTEGER NOT NULL UNIQUE,
    [tweet_id] TEXT NOT NULL,
    [tweet_text] TEXT,
    [tweet_via] TEXT,
    [tweet_url] TEXT NOT NULL,
    [external_link_url] TEXT NOT NULL,
    [external_link_type] TEXT,
    [created_at] TEXT NOT NULL,
    [appeared_at] TEXT NOT NULL,
    [registered_at] TEXT NOT NULL,
    PRIMARY KEY([id])
    """

    __tablename__ = "ExternalLink"

    id = Column(Integer, primary_key=True)
    tweet_id = Column(String(256), nullable=False, unique=True)
    tweet_text = Column(String(256))
    tweet_via = Column(String(256))
    tweet_url = Column(String(256), nullable=False)
    external_link_url = Column(String(256), nullable=False)
    external_link_type = Column(String(256))
    created_at = Column(String(256), nullable=False)
    appeared_at = Column(String(256), nullable=False)
    registered_at = Column(String(256), nullable=False)

    def __init__(
        self,
        tweet_id: str,
        tweet_text: str,
        tweet_via: str,
        tweet_url: str,
        external_link_url: str,
        external_link_type: str,
        created_at: str,
        appeared_at: str,
        registered_at: str,
    ):
        # self.id = id
        self.tweet_id = tweet_id
        self.tweet_text = tweet_text
        self.tweet_via = tweet_via
        self.tweet_url = tweet_url
        self.external_link_url = external_link_url
        self.external_link_type = external_link_type
        self.created_at = created_at
        self.appeared_at = appeared_at
        self.registered_at = registered_at

    @classmethod
    def create(self, args_dict: dict) -> Self:
        match args_dict:
            case {
                "tweet_id": tweet_id,
                "tweet_text": tweet_text,
                "tweet_via": tweet_via,
                "tweet_url": tweet_url,
                "external_link_url": external_link_url,
                "external_link_type": external_link_type,
                "created_at": created_at,
                "appeared_at": appeared_at,
                "registered_at": registered_at,
            }:
                return ExternalLink(
                    tweet_id,
                    tweet_text,
                    tweet_via,
                    tweet_url,
                    external_link_url,
                    external_link_type,
                    created_at,
                    appeared_at,
                    registered_at,
                )
            case _:
                raise ValueError("Unmatch args_dict.")

    def __repr__(self):
        return f"<ExternalLink(external_link_url='{self.external_link_url}')>"

    def __eq__(self, other):
        return (
            isinstance(other, ExternalLink)
            and other.external_link_url == self.external_link_url
            and other.tweet_id == self.tweet_id
        )

    def to_dict(self) -> dict:
        return {
            "tweet_id": self.tweet_id,
            "tweet_text": self.tweet_text,
            "tweet_via": self.tweet_via,
            "tweet_url": self.tweet_url,
            "external_link_url": self.external_link_url,
            "external_link_type": self.external_link_type,
            "created_at": self.created_at,
            "appeared_at": self.appeared_at,
            "registered_at": self.registered_at,
        }


class Metric(Base):
    """数値指標系モデル
    [id] INTEGER NOT NULL UNIQUE,
    [screen_name] TEXT NOT NULL,
    [status_count] INTEGER NOT NULL,
    [favorite_count] INTEGER NOT NULL,
    [media_count] INTEGER NOT NULL,
    [following_count] INTEGER NOT NULL,
    [followers_count] INTEGER NOT NULL,
    [min_appeared_at] TEXT NOT NULL,
    [max_appeared_at] TEXT NOT NULL,
    [duration_days] INTEGER NOT NULL,
    [count_all] INTEGER NOT NULL,
    [appeared_days] INTEGER NOT NULL,
    [non_appeared_days] INTEGER NOT NULL,
    [average_tweet_by_day] NUMERIC NOT NULL,
    [max_tweet_num_by_day] INTEGER NOT NULL,
    [max_tweet_day_by_day] TEXT NOT NULL,
    [tweet_length_sum] INTEGER NOT NULL,
    [tweet_length_by_count] NUMERIC NOT NULL,
    [tweet_length_by_day] NUMERIC NOT NULL,
    [communication_ratio] NUMERIC NOT NULL,
    [increase_following_by_day] NUMERIC NOT NULL,
    [increase_followers_by_day] NUMERIC NOT NULL,
    [ff_ratio] NUMERIC NOT NULL,
    [ff_ratio_inverse] NUMERIC NOT NULL,
    [available_following] INTEGER NOT NULL,
    [rest_available_following] INTEGER NOT NULL,
    [registered_at] TEXT NOT NULL,
    PRIMARY KEY([id])
    """

    __tablename__ = "Metric"

    id = Column(Integer, primary_key=True)
    screen_name = Column(String(256), nullable=False)
    status_count = Column(Integer, nullable=False)
    favorite_count = Column(Integer, nullable=False)
    media_count = Column(Integer, nullable=False)
    following_count = Column(Integer, nullable=False)
    followers_count = Column(Integer, nullable=False)
    min_appeared_at = Column(String(256), nullable=False)
    max_appeared_at = Column(String(256), nullable=False)
    duration_days = Column(Integer, nullable=False)
    count_all = Column(Integer, nullable=False)
    appeared_days = Column(Integer, nullable=False)
    non_appeared_days = Column(Integer, nullable=False)
    average_tweet_by_day = Column(Numeric, nullable=False)
    max_tweet_num_by_day = Column(Integer, nullable=False)
    max_tweet_day_by_day = Column(String(256), nullable=False)
    tweet_length_sum = Column(Integer, nullable=False)
    tweet_length_by_count = Column(Numeric, nullable=False)
    tweet_length_by_day = Column(Numeric, nullable=False)
    communication_ratio = Column(Numeric, nullable=False)
    increase_following_by_day = Column(Numeric, nullable=False)
    increase_followers_by_day = Column(Numeric, nullable=False)
    ff_ratio = Column(Numeric, nullable=False)
    ff_ratio_inverse = Column(Numeric, nullable=False)
    available_following = Column(Integer, nullable=False)
    rest_available_following = Column(Integer, nullable=False)
    registered_at = Column(String(256), nullable=False)

    def __init__(
        self,
        screen_name: str,
        status_count: int,
        favorite_count: int,
        media_count: int,
        following_count: int,
        followers_count: int,
        min_appeared_at: str,
        max_appeared_at: str,
        duration_days: int,
        count_all: int,
        appeared_days: int,
        non_appeared_days: int,
        average_tweet_by_day: float,
        max_tweet_num_by_day: int,
        max_tweet_day_by_day: str,
        tweet_length_sum: int,
        tweet_length_by_count: float,
        tweet_length_by_day: float,
        communication_ratio: float,
        increase_following_by_day: float,
        increase_followers_by_day: float,
        ff_ratio: float,
        ff_ratio_inverse: float,
        available_following: int,
        rest_available_following: int,
        registered_at: str,
    ):
        # self.id = id
        self.screen_name = screen_name
        self.status_count = status_count
        self.favorite_count = favorite_count
        self.media_count = media_count
        self.following_count = following_count
        self.followers_count = followers_count
        self.min_appeared_at = min_appeared_at
        self.max_appeared_at = max_appeared_at
        self.duration_days = duration_days
        self.count_all = count_all
        self.appeared_days = appeared_days
        self.non_appeared_days = non_appeared_days
        self.average_tweet_by_day = average_tweet_by_day
        self.max_tweet_num_by_day = max_tweet_num_by_day
        self.max_tweet_day_by_day = max_tweet_day_by_day
        self.tweet_length_sum = tweet_length_sum
        self.tweet_length_by_count = tweet_length_by_count
        self.tweet_length_by_day = tweet_length_by_day
        self.communication_ratio = communication_ratio
        self.increase_following_by_day = increase_following_by_day
        self.increase_followers_by_day = increase_followers_by_day
        self.ff_ratio = ff_ratio
        self.ff_ratio_inverse = ff_ratio_inverse
        self.available_following = available_following
        self.rest_available_following = rest_available_following
        self.registered_at = registered_at

    @classmethod
    def create(self, args_dict: dict) -> Self:
        match args_dict:
            case {
                "screen_name": screen_name,
                "status_count": status_count,
                "favorite_count": favorite_count,
                "media_count": media_count,
                "following_count": following_count,
                "followers_count": followers_count,
                "min_appeared_at": min_appeared_at,
                "max_appeared_at": max_appeared_at,
                "duration_days": duration_days,
                "count_all": count_all,
                "appeared_days": appeared_days,
                "non_appeared_days": non_appeared_days,
                "average_tweet_by_day": average_tweet_by_day,
                "max_tweet_num_by_day": max_tweet_num_by_day,
                "max_tweet_day_by_day": max_tweet_day_by_day,
                "tweet_length_sum": tweet_length_sum,
                "tweet_length_by_count": tweet_length_by_count,
                "tweet_length_by_day": tweet_length_by_day,
                "communication_ratio": communication_ratio,
                "increase_following_by_day": increase_following_by_day,
                "increase_followers_by_day": increase_followers_by_day,
                "ff_ratio": ff_ratio,
                "ff_ratio_inverse": ff_ratio_inverse,
                "available_following": available_following,
                "rest_available_following": rest_available_following,
                "registered_at": registered_at,
            }:
                return Metric(
                    screen_name,
                    status_count,
                    favorite_count,
                    media_count,
                    following_count,
                    followers_count,
                    min_appeared_at,
                    max_appeared_at,
                    duration_days,
                    count_all,
                    appeared_days,
                    non_appeared_days,
                    average_tweet_by_day,
                    max_tweet_num_by_day,
                    max_tweet_day_by_day,
                    tweet_length_sum,
                    tweet_length_by_count,
                    tweet_length_by_day,
                    communication_ratio,
                    increase_following_by_day,
                    increase_followers_by_day,
                    ff_ratio,
                    ff_ratio_inverse,
                    available_following,
                    rest_available_following,
                    registered_at,
                )
            case _:
                raise ValueError("Unmatch args_dict.")

    def __repr__(self) -> str:
        return f"<Metric(registered_at='{self.registered_at}')>"

    def __eq__(self, other) -> bool:
        return (
            isinstance(other, Metric)
            and other.screen_name == self.screen_name
            and other.registered_at == self.registered_at
        )

    def to_dict(self) -> dict:
        return {
            "screen_name": self.screen_name,
            "status_count": self.status_count,
            "favorite_count": self.favorite_count,
            "media_count": self.media_count,
            "following_count": self.following_count,
            "followers_count": self.followers_count,
            "min_appeared_at": self.min_appeared_at,
            "max_appeared_at": self.max_appeared_at,
            "duration_days": self.duration_days,
            "count_all": self.count_all,
            "appeared_days": self.appeared_days,
            "non_appeared_days": self.non_appeared_days,
            "average_tweet_by_day": self.average_tweet_by_day,
            "max_tweet_num_by_day": self.max_tweet_num_by_day,
            "max_tweet_day_by_day": self.max_tweet_day_by_day,
            "tweet_length_sum": self.tweet_length_sum,
            "tweet_length_by_count": self.tweet_length_by_count,
            "tweet_length_by_day": self.tweet_length_by_day,
            "communication_ratio": self.communication_ratio,
            "increase_following_by_day": self.increase_following_by_day,
            "increase_followers_by_day": self.increase_followers_by_day,
            "ff_ratio": self.ff_ratio,
            "ff_ratio_inverse": self.ff_ratio_inverse,
            "available_following": self.available_following,
            "rest_available_following": self.rest_available_following,
            "registered_at": self.registered_at,
        }


if __name__ == "__main__":
    test_db = Path("./test_DB.db")
    test_db.unlink(missing_ok=True)
    engine = create_engine(f"sqlite:///{test_db.name}", echo=True)
    Base.metadata.create_all(engine)

    session = Session(engine)
    session.query(Tweet).delete()

    num = 10
    now_date = datetime.now()
    tweet_dict_list = [
        {
            "tweet_id": f"{i}",
            "tweet_text": f"test_{i}",
            "tweet_via": f"test_via_{i}",
            "tweet_url": f"test_url_{i}",
            "user_id": f"user_{i}",
            "user_name": f"user_name_{i}",
            "screen_name": f"screen_name_{i}",
            "is_retweet": False,
            "retweet_tweet_id": "",
            "is_quote": False,
            "quote_tweet_id": "",
            "has_media": False,
            "created_at": now_date.isoformat(),
        }
        for i in range(num)
    ]
    record_list = [Tweet.create(tweet_dict) for tweet_dict in tweet_dict_list]
    for record in record_list:
        session.add(record)
    session.commit()

    media_dict_list = [
        {
            "tweet_id": f"{i}",
            "media_filename": f"media_filename_{i}",
            "media_url": f"media_url_{i}",
            "media_type": f"photo",
            "media_size": int(i * 10),
            "created_at": now_date.isoformat(),
        }
        for i in range(num)
    ]
    record_list = [Media.create(media_dict) for media_dict in media_dict_list]
    for record in record_list:
        session.add(record)
    session.commit()

    metric_dict_list = [
        {
            "status_count": int(i * 10),
            "favorite_count": int(i * 10),
            "media_count": int(i * 10),
            "following_count": int(i * 10),
            "followers_count": int(i * 10),
            "created_at": now_date.isoformat(),
        }
        for i in range(num)
    ]
    record_list = [Metric.create(metric_dict) for metric_dict in metric_dict_list]
    for record in record_list:
        session.add(record)
    session.commit()

    external_link_dict_list = [
        {
            "tweet_id": f"{i}",
            "external_link_url": f"url_{i}",
            "external_link_type": f"type_{i}",
            "created_at": now_date.isoformat(),
        }
        for i in range(num)
    ]
    record_list = [ExternalLink.create(external_link_dict) for external_link_dict in external_link_dict_list]
    for record in record_list:
        session.add(record)
    session.commit()

    result = session.query(Tweet).all()[:10]
    for f in result:
        print(f)

    session.close()
    # test_db.unlink(missing_ok=True)
