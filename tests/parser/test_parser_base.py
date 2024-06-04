import sys
import unittest
import urllib.parse
from contextlib import ExitStack
from datetime import datetime, timedelta
from pathlib import Path

import orjson
from mock import MagicMock, patch

from personal_twilog.parser.parser_base import ParserBase
from personal_twilog.util import find_values


class ConcreteParser(ParserBase):
    def parse(self):
        return "parse called"


class TestParserBase(unittest.TestCase):
    def get_json_dict(self) -> dict:
        return orjson.loads(Path("./tests/cache/timeline_sample.json").read_bytes())

    def get_instance(self) -> ConcreteParser:
        timeline_dict = self.get_json_dict()
        entry_list: list[dict] = find_values(timeline_dict, "entries")
        tweet_dict_list: list[dict] = find_values(entry_list, "tweet_results")
        registered_at = "2023-10-07T01:00:00"
        parser = ConcreteParser(tweet_dict_list, registered_at)
        return parser

    def test_init(self):
        timeline_dict = self.get_json_dict()
        entry_list: list[dict] = find_values(timeline_dict, "entries")
        tweet_dict_list: list[dict] = find_values(entry_list, "tweet_results")
        registered_at = "2023-10-07T01:00:00"

        actual = ConcreteParser(tweet_dict_list, registered_at)
        self.assertEqual(tweet_dict_list, actual.tweet_dict_list)
        self.assertEqual(tweet_dict_list, actual.result)
        self.assertEqual("2023-10-07T01:00:00", actual.registered_at)
        self.assertEqual("parse called", actual.parse())

        with self.assertRaises(TypeError):
            actual = ConcreteParser("invalid_args", registered_at)
        with self.assertRaises(TypeError):
            actual = ConcreteParser(["invalid_args"], registered_at)
        with self.assertRaises(TypeError):
            actual = ConcreteParser(tweet_dict_list, -1)

    def test_remove_duplicates(self):
        parser = self.get_instance()

        MAX_NUM = 10
        sample_list = [{"tweet_id": f"{i}{i:04}"} for i in range(MAX_NUM)]

        actual = parser._remove_duplicates(sample_list)
        expect = sample_list
        self.assertEqual(expect, actual)

        sample_list2 = []
        sample_list2.extend(sample_list)
        sample_list2.extend(sample_list)
        actual = parser._remove_duplicates(sample_list2)
        expect = sample_list
        self.assertEqual(expect, actual)

        sample_list3 = []
        sample_list3.extend(sample_list)
        sample_list3.extend(sample_list[: MAX_NUM // 2])
        actual = parser._remove_duplicates(sample_list3)
        expect = sample_list
        self.assertEqual(expect, actual)

        with self.assertRaises(TypeError):
            actual = parser._remove_duplicates(-1)
        with self.assertRaises(TypeError):
            actual = parser._remove_duplicates([sample_list[0], -1])
        with self.assertRaises(ValueError):
            actual = parser._remove_duplicates([sample_list[0], {}])

    def test_get_external_link_type(self):
        parser = self.get_instance()
        url = "https://www.pixiv.net/artworks/99999999"
        actual = parser._get_external_link_type(url)
        self.assertEqual("pixiv", actual)

        url = "https://www.pixiv.net/novel/show.php?id=99999999"
        actual = parser._get_external_link_type(url)
        self.assertEqual("pixiv_novel", actual)

        url = "https://nijie.info/view.php?id=99999999"
        actual = parser._get_external_link_type(url)
        self.assertEqual("nijie", actual)

        url = "https://nijie.info/view_popup.php?id=99999999"
        actual = parser._get_external_link_type(url)
        self.assertEqual("nijie", actual)

        url = "https://seiga.nicovideo.jp/seiga/im99999999"
        actual = parser._get_external_link_type(url)
        self.assertEqual("nico_seiga", actual)

        url = "http://nico.ms/im99999999"
        actual = parser._get_external_link_type(url)
        self.assertEqual("nico_seiga", actual)

        url = "https://skeb.jp/@author1/works/99999999"
        actual = parser._get_external_link_type(url)
        self.assertEqual("skeb", actual)

        url = ""
        actual = parser._get_external_link_type(url)
        self.assertEqual("", actual)

        url = "https://www.google.co.jp/"
        actual = parser._get_external_link_type(url)
        self.assertEqual("", actual)

        with self.assertRaises(TypeError):
            actual = parser._get_external_link_type(-1)

    def test_match_entities(self):
        parser = self.get_instance()
        timeline_dict = self.get_json_dict()

        entities_list = find_values(timeline_dict, "entities")
        for entities in entities_list:
            expanded_urls = find_values(entities, "expanded_url")
            actual = parser._match_entities(entities)
            if expanded_urls:
                self.assertEqual({"expanded_urls": expanded_urls}, actual)
            else:
                self.assertEqual({}, actual)

        actual = parser._match_entities({})
        self.assertEqual({}, actual)

        with self.assertRaises(TypeError):
            actual = parser._match_entities(-1)

    def test_match_media(self):
        parser = self.get_instance()
        timeline_dict = self.get_json_dict()
        media_dict_list = find_values(timeline_dict, "media")

        def match_media(media: dict) -> dict:
            match media:
                case {
                    "type": "photo",
                    "media_url_https": media_url,
                }:
                    media_filename = Path(media_url).name
                    media_thumbnail_url = media_url + ":large"
                    media_url = media_url + ":orig"
                    result = {
                        "media_filename": media_filename,
                        "media_url": media_url,
                        "media_thumbnail_url": media_thumbnail_url,
                        "media_type": media.get("type", "photo"),
                    }
                    return result
                case {
                    "type": "video" | "animated_gif",
                    "video_info": {"variants": video_variants},
                    "media_url_https": media_thumbnail_url,
                }:
                    media_url = ""
                    bitrate = -sys.maxsize  # 最小値
                    for video_variant in video_variants:
                        if video_variant["content_type"] == "video/mp4":
                            if int(video_variant["bitrate"]) > bitrate:
                                media_url = video_variant["url"]
                                bitrate = int(video_variant["bitrate"])
                    url_path = Path(urllib.parse.urlparse(media_url).path)
                    media_url = urllib.parse.urljoin(media_url, url_path.name)
                    media_filename = Path(media_url).name
                    media_thumbnail_url = media_thumbnail_url + ":orig"
                    result = {
                        "media_filename": media_filename,
                        "media_url": media_url,
                        "media_thumbnail_url": media_thumbnail_url,
                        "media_type": media.get("type", "video"),
                    }
                    return result

        for media_list in media_dict_list:
            for media in media_list:
                actual = parser._match_media(media)
                expect = match_media(media)
                self.assertEqual(expect, actual)

        with self.assertRaises(TypeError):
            actual = parser._match_media(-1)

    def test_get_media_size(self):
        with ExitStack() as stack:
            mock_requests = stack.enter_context(patch("personal_twilog.parser.parser_base.requests"))

            def return_head(media_url):
                mock_head_response = MagicMock()
                mock_head_response.headers = {"Content-Length": len(media_url)}
                return mock_head_response

            mock_requests.head.side_effect = return_head

            parser = self.get_instance()
            url = "https://pbs.twimg.com/ext_tw_video_thumb/90000000/pu/img/90000000.jpg"
            actual = parser._get_media_size(url)
            expect = len(url)
            self.assertEqual(expect, actual)
            mock_requests.head.assert_called_once_with(url)

            def return_head(media_url):
                mock_head_response = MagicMock()
                mock_head_response.headers = {}
                return mock_head_response

            mock_requests.head.side_effect = return_head
            actual = parser._get_media_size(url)
            self.assertEqual(0, actual)

            def return_head(media_url):
                mock_head_response = MagicMock()
                mock_head_response.raise_for_status.side_effect = ValueError
                return mock_head_response

            mock_requests.head.side_effect = return_head
            actual = parser._get_media_size(url)
            self.assertEqual(-1, actual)

    def test_match_rt_quote(self):
        parser = self.get_instance()
        timeline_dict = self.get_json_dict()
        tweet_results_list = find_values(timeline_dict, "tweet_results")
        tweet_list = [t.get("result") for t in tweet_results_list]

        def match_rt_quote(tweet):
            retweet_tweet = {}
            quote_tweet = {}
            match tweet:
                case {
                    "legacy": {
                        "retweeted_status_result": {
                            "result": tweet_result,
                        },
                    },
                }:
                    retweet_tweet = tweet_result
            match tweet:
                case {
                    "quoted_status_result": {
                        "result": tweet_result,
                    },
                }:
                    quote_tweet = tweet_result
            match tweet:
                case {
                    "legacy": {
                        "retweeted_status_result": {
                            "result": {
                                "rest_id": _,
                                "quoted_status_result": {
                                    "result": quote_tweet_result,
                                },
                            },
                        },
                    },
                }:
                    retweet_tweet_result = tweet.get("legacy", {}).get("retweeted_status_result", {}).get("result", {})
                    retweet_tweet = retweet_tweet_result
                    quote_tweet = quote_tweet_result
            return (retweet_tweet, quote_tweet)

        for tweet in tweet_list:
            actual = parser._match_rt_quote(tweet)
            expect = match_rt_quote(tweet)
            self.assertEqual(expect, actual)

        with self.assertRaises(TypeError):
            actual = parser._match_rt_quote(-1)

    def test_get_created_at(self):
        parser = self.get_instance()
        timeline_dict = self.get_json_dict()
        tweet_results_list = find_values(timeline_dict, "tweet_results")
        tweet_list = [t.get("result") for t in tweet_results_list]

        def to_jst(source_date_str):
            td_format = "%a %b %d %H:%M:%S +0000 %Y"
            created_at_gmt = datetime.strptime(source_date_str, td_format)
            created_at_jst = created_at_gmt + timedelta(hours=9)
            created_at = created_at_jst.isoformat()
            return created_at

        created_at_list = [to_jst(d) for d in find_values(tweet_list, "created_at", False, ["legacy"])]
        for tweet, expect in zip(tweet_list, created_at_list):
            actual = parser._get_created_at(tweet)
            self.assertEqual(expect, actual)

    def test_flatten(self):
        parser = self.get_instance()
        timeline_dict = self.get_json_dict()
        tweet_results_list = find_values(timeline_dict, "tweet_results")
        actual = parser._flatten(tweet_results_list)

        def flatten(tweet_list: list[dict]) -> list[dict]:
            edited_tweet_list: list[dict] = []
            flattened_tweet_list: list[dict] = []
            for tweet in tweet_list:
                tweet = tweet.get("result", {})
                if tweet.get("__typename", "") == "TweetWithVisibilityResults":
                    tweet = tweet.get("tweet", {})
                if tweet.get("__typename", "") == "TweetTombstone":
                    continue
                retweet_tweet, quote_tweet = parser._match_rt_quote(tweet)

                appeared_at = parser._get_created_at(tweet)
                tweet["appeared_at"] = appeared_at

                flattened_tweet_list.append(tweet)

                if retweet_tweet:
                    retweet_tweet["appeared_at"] = appeared_at
                    flattened_tweet_list.append(retweet_tweet)
                if quote_tweet:
                    quote_tweet["appeared_at"] = appeared_at
                    flattened_tweet_list.append(quote_tweet)

            for tweet in flattened_tweet_list:
                if tweet.get("__typename", "") == "TweetWithVisibilityResults":
                    appeared_at = tweet.get("appeared_at", "")
                    tweet = tweet.get("tweet", {})
                    tweet["appeared_at"] = appeared_at
                if tweet.get("__typename", "") == "TweetTombstone":
                    continue
                match tweet:
                    case {
                        "core": {
                            "user_results": {
                                "result": {
                                    "legacy": l1,
                                }
                            }
                        },
                        "legacy": l2,
                        "rest_id": rest_id,
                        "source": source,
                    } if l1 != {} and l2 != {} and rest_id != "" and source != "":
                        pass
                    case _:
                        raise ValueError("flatten failed. invalid '__typename' or structure.")
                edited_tweet_list.append(tweet)
            return edited_tweet_list

        actual = parser._flatten(tweet_results_list)
        expect = flatten(tweet_results_list)
        self.assertEqual(expect, actual)


def make_sample_file():
    def make_entities(i: int, is_external_link: bool):
        if not is_external_link:
            return {"entities": {"user_mentions": [], "urls": [], "hashtags": [], "symbols": []}}
        external_link = f"https://www.pixiv.net/artworks/{i:08}"
        return {
            "entities": {
                "description": {"urls": []},
                "url": {
                    "urls": [
                        {"display_url": "display_url", "expanded_url": external_link, "url": "url", "indices": [0, 23]}
                    ]
                },
            }
        }

    def make_media(i: int, screen_name: str, photo_num: int, video_num: int):
        d = {"media": []}
        for j in range(photo_num):
            d["media"].append({
                "display_url": f"pic.twitter.com/{j:08}",
                "expanded_url": f"https://twitter.com/{screen_name}/status/{i}{j:07}/photo/1",
                "id_str": f"{i:08}",
                "indices": [0, 10],
                "media_key": f"{i:08}",
                "media_url_https": f"https://pbs.twimg.com/media/{i}{j:07}.jpg",
                "source_status_id_str": f"{i:08}",
                "source_user_id_str": f"{i:08}",
                "type": "photo",
                "url": f"https://t.co/{j:08}",
                "ext_media_availability": {"status": "Available"},
            })
        for j in range(video_num):
            d["media"].append({
                "display_url": f"pic.twitter.com/{j:08}",
                "expanded_url": f"https://twitter.com/{screen_name}/status/{i}{j:07}/video/1",
                "id_str": f"{i:08}",
                "indices": [0, 10],
                "media_key": f"{i:08}",
                "media_url_https": f"https://pbs.twimg.com/ext_tw_video_thumb/{i}{j:07}/pu/img/{i}{j:07}.jpg",
                "type": "video",
                "url": "https://t.co/{j:08}",
                "video_info": {
                    "aspect_ratio": [16, 9],
                    "duration_millis": 16726,
                    "variants": [
                        {
                            "bitrate": 50000,
                            "content_type": "video/mp4",
                            "url": f"https://video.twimg.com/ext_tw_video/{i}{j:07}/pu/vid/1280x720/{i}{j:07}.mp4?tag=12",
                        },
                        {
                            "bitrate": 2000,
                            "content_type": "video/mp4",
                            "url": f"https://video.twimg.com/ext_tw_video/{i}{j:07}/pu/vid/640x360/{i}{j:07}.mp4?tag=12",
                        },
                        {
                            "bitrate": 100,
                            "content_type": "video/mp4",
                            "url": f"https://video.twimg.com/ext_tw_video/{i}{j:07}/pu/vid/480x270/{i}{j:07}.mp4?tag=12",
                        },
                        {
                            "content_type": "application/x-mpegURL",
                            "url": f"https://video.twimg.com/ext_tw_video/{i}{j:07}/pu/pl/{i}{j:07}.m3u8?tag=12&container=fmp4",
                        },
                    ],
                },
            })
        return d

    def make_user_results(user_rest_id: str, user_name: str, screen_name: str):
        i = int(user_rest_id[0])
        return {
            "user_results": {
                "result": {
                    "rest_id": user_rest_id,
                    "legacy": {
                        "name": user_name,
                        "screen_name": screen_name,
                        "statuses_count": i * 100,
                        "favourites_count": i * 50,
                        "media_count": i * 30,
                        "friends_count": i * 10,
                        "followers_count": i * 10,
                    },
                }
            }
        }

    def make_tweet(
        id_str: str, screen_name: str, is_rt: bool, is_qt: bool, is_external_link: bool, photo_num: int, video_num: int
    ):
        i = int(id_str[0])
        is_media = (photo_num > 0) or (video_num > 0)
        d2 = {
            "rest_id": id_str,
            "source": '<a href="https://mobile.twitter.com" rel="nofollow">Twitter Web App</a>',
        }
        user_rest_id = id_str[:-2] + id_str[-1] + id_str[-1]
        core = make_user_results(user_rest_id, f"user_name_{i:02}", screen_name)
        legacy = {
            "created_at": f"Wed Aug 07 01:00:{i:02} +0000 2023",
            "full_text": f"full_text_{i:02}",
            "id_str": id_str,
            "entities": make_entities(i, is_external_link)["entities"],
        }
        if is_media:
            legacy["extended_entities"] = {
                "media": make_media(i, f"{screen_name}_media", photo_num, video_num)["media"]
            }

        if is_rt and is_qt:
            rt_id_str = id_str[0] + id_str[0] + id_str[2:]
            qt_id_str = id_str[0] + id_str[1] + id_str[0] + id_str[3:]
            t = make_tweet(qt_id_str, f"{screen_name}_rt_qt", False, False, False, photo_num, video_num)[
                "tweet_results"
            ]["result"]
            legacy["retweeted_status_result"] = {
                "result": {
                    "quoted_status_result": {
                        "result": t,
                    },
                }
                | t
                | {"rest_id": rt_id_str},
            }
        elif is_qt:
            qt_id_str = id_str[0] + id_str[1] + id_str[0] + id_str[3:]
            d2["quoted_status_result"] = {
                "result": make_tweet(qt_id_str, f"{screen_name}_qt", False, False, False, photo_num, video_num)[
                    "tweet_results"
                ]["result"]
            }
        elif is_rt:
            rt_id_str = id_str[0] + id_str[0] + id_str[2:]
            legacy["retweeted_status_result"] = {
                "result": make_tweet(rt_id_str, f"{screen_name}_rt", False, False, False, photo_num, video_num)[
                    "tweet_results"
                ]["result"]
            }

        d2["core"] = core
        d2["legacy"] = legacy
        d = {"tweet_results": {"result": d2}}
        return d

    def make_entry(
        i: int, screen_name: str, is_rt: bool, is_qt: bool, is_external_link: bool, photo_num: int, video_num: int
    ):
        id_str = f"{i}{i:04}"
        return {
            "content": {
                "entryType": "TimelineTimelineItem",
                "__typename": "TimelineTimelineItem",
                "itemContent": {
                    "itemType": "TimelineTweet",
                    "__typename": "TimelineTweet",
                    "tweet_results": make_tweet(
                        id_str, screen_name, is_rt, is_qt, is_external_link, photo_num, video_num
                    )["tweet_results"],
                },
            }
        }

    def make_timeline():
        args = [
            (1, "screen_name_1", False, False, False, 0, 0),
            (2, "screen_name_2", False, False, False, 4, 0),
            (3, "screen_name_3", False, False, False, 0, 4),
            (4, "screen_name_4", False, False, False, 2, 2),
            (5, "screen_name_5", True, False, False, 2, 2),
            (6, "screen_name_6", False, True, False, 2, 2),
            (7, "screen_name_7", True, True, False, 2, 2),
            (8, "screen_name_8", False, False, True, 0, 0),
            (9, "screen_name_9", False, False, True, 2, 2),
        ]
        entries = [make_entry(*v) for v in args]
        return {
            "data": {
                "user": {
                    "result": {
                        "__typename": "User",
                        "timeline_v2": {
                            "timeline": {
                                "instructions": [
                                    {
                                        "type": "TimelineAddEntries",
                                        "entries": entries,
                                    }
                                ]
                            }
                        },
                    }
                }
            }
        }

    Path("./tests/cache/timeline_sample.json").write_bytes(orjson.dumps(make_timeline(), option=orjson.OPT_INDENT_2))


if __name__ == "__main__":
    if sys.argv:
        del sys.argv[1:]
    unittest.main(warnings="ignore")

    # make_sample_file()
    pass
