from datetime import datetime
from datetime import timedelta
from json import load
from pathlib import Path
from re import sub
from typing import Optional

from pytest import fixture
from pytest import raises
from requests.cookies import RequestsCookieJar

import faapi
from faapi import Comment
from faapi import FAAPI
from faapi import JournalPartial
from faapi import SubmissionPartial
from faapi import UserPartial
from faapi.exceptions import DisallowedPath
from faapi.exceptions import Unauthorized
from faapi.parse import username_url
from test_parse import clean_html

__root__: Path = Path(__file__).resolve().parent


@fixture
def data() -> dict:
    return load((__root__ / "test_data.json").open())


@fixture
def cookies(data: dict) -> RequestsCookieJar:
    return data["cookies"]


@fixture
def user_test_data() -> dict:
    return load((__root__ / "test_user.json").open())


@fixture
def submission_test_data() -> dict:
    return load((__root__ / "test_submission.json").open())


@fixture
def journal_test_data() -> dict:
    return load((__root__ / "test_journal.json").open())


def dst_us() -> timedelta:
    now: datetime = datetime.now()

    if now.month < 3 or now.month >= 12:
        return timedelta(0)

    m1 = datetime(now.year, 3, 1)

    if now < datetime(now.year, 3, 7 + (6 - m1.weekday() + 1)):
        return timedelta(0)

    n1 = datetime(now.year, 11, 1)

    if now > datetime(now.year, 11, 6 - n1.weekday() + 1):
        return timedelta(0)

    return timedelta(hours=-1)


def remove_user_icons(html: str) -> str:
    return sub(r"a\.furaffinity\.net/\d{8}/[^. ]+.gif", "", html)


def test_robots(cookies: RequestsCookieJar):
    api: FAAPI = FAAPI(cookies)
    assert getattr(api.robots, "default_entry") is not None
    assert api.crawl_delay >= 1
    assert api.check_path("/login")
    assert api.check_path("/view")
    assert api.check_path("/journal")
    assert api.check_path("/user")
    assert api.check_path("/gallery")
    assert api.check_path("/scraps")
    assert api.check_path("/favorite")
    assert api.check_path("/journals")
    assert api.check_path("/watchlist/to")
    assert api.check_path("/watchlist/by")
    with raises(DisallowedPath):
        assert not api.check_path("/fav/", raise_for_disallowed=True)


def test_login(cookies: RequestsCookieJar):
    api: FAAPI = FAAPI(cookies)
    assert api.login_status
    assert api.connection_status

    api.load_cookies([{"name": "a", "value": "1"}])
    with raises(Unauthorized):
        api.me()


# noinspection DuplicatedCode
def test_frontpage(cookies: RequestsCookieJar):
    api: FAAPI = FAAPI(cookies)

    ss = api.frontpage()

    assert len({s.id for s in ss}) == len(ss)

    for submission in ss:
        assert submission.id > 0
        assert submission.type != ""
        assert submission.rating != ""
        assert submission.thumbnail_url != ""


def test_user(cookies: RequestsCookieJar, user_test_data: dict):
    api: FAAPI = FAAPI(cookies)

    user = api.user(user_test_data["name"])
    user_dict = dict(user)

    assert user.name.lower() == user_dict["name"].lower() == user_test_data["name"].lower()
    assert user.status == user_dict["status"] == user_test_data["status"]
    assert user.title == user_dict["title"] == user_test_data["title"]
    assert user.join_date == user_dict["join_date"] == datetime.fromisoformat(user_test_data["join_date"]) + dst_us()
    assert user.stats.views == user_dict["stats"]["views"]
    assert user_dict["stats"]["views"] >= user_test_data["stats"]["views"]
    assert user.stats.submissions == user_dict["stats"]["submissions"]
    assert user_dict["stats"]["submissions"] >= user_test_data["stats"]["submissions"]
    assert user.stats.favorites == user_dict["stats"]["favorites"]
    assert user_dict["stats"]["favorites"] >= user_test_data["stats"]["favorites"]
    assert user.stats.comments_earned == user_dict["stats"]["comments_earned"]
    assert user_dict["stats"]["comments_earned"] >= user_test_data["stats"]["comments_earned"]
    assert user.stats.comments_made == user_dict["stats"]["comments_made"]
    assert user_dict["stats"]["comments_made"] >= user_test_data["stats"]["comments_made"]
    assert user.stats.journals == user_dict["stats"]["journals"]
    assert user_dict["stats"]["journals"] >= user_test_data["stats"]["journals"]
    assert user.info == user_dict["info"] == user_test_data["info"]
    assert user.contacts == user_dict["contacts"] == user_test_data["contacts"]
    assert user.avatar_url == user_dict["avatar_url"] != ""
    assert user.banner_url == user_dict["banner_url"] != ""
    assert remove_user_icons(clean_html(user.profile)) == \
           remove_user_icons(clean_html(user_dict["profile"])) == \
           remove_user_icons(clean_html(user_test_data["profile"]))
    assert user.profile_bbcode == user_test_data["profile_bbcode"]


# noinspection DuplicatedCode
def test_submission(cookies: RequestsCookieJar, submission_test_data: dict):
    api: FAAPI = FAAPI(cookies)

    submission, file = api.submission(submission_test_data["id"], get_file=True)
    submission_dict = dict(submission)

    assert submission.id == submission_dict["id"] == submission_test_data["id"]
    assert submission.title == submission_dict["title"] == submission_test_data["title"]
    assert submission.author.name.lower() == submission_dict["author"]["name"].lower() == submission_test_data["author"]["name"].lower()
    assert submission.author.avatar_url == submission_dict["author"]["avatar_url"] != ""
    assert submission.date == submission_dict["date"] == datetime.fromisoformat(submission_test_data["date"]) + dst_us()
    assert submission.tags == submission_dict["tags"] == submission_test_data["tags"]
    assert submission.category == submission_dict["category"] == submission_test_data["category"]
    assert submission.species == submission_dict["species"] == submission_test_data["species"]
    assert submission.gender == submission_dict["gender"] == submission_test_data["gender"]
    assert submission.rating == submission_dict["rating"] == submission_test_data["rating"]
    assert submission.stats.views == submission_dict["stats"]["views"]
    assert submission.stats.views >= submission_test_data["stats"]["views"]
    assert submission.stats.comments == submission_dict["stats"]["comments"]
    assert submission.stats.comments >= submission_test_data["stats"]["comments"]
    assert submission.stats.favorites == submission_dict["stats"]["favorites"]
    assert submission.stats.favorites >= submission_test_data["stats"]["favorites"]
    assert submission.type == submission_dict["type"] == submission_test_data["type"]
    assert submission.mentions == submission_dict["mentions"] == submission_test_data["mentions"]
    assert submission.folder == submission_dict["folder"] == submission_test_data["folder"]
    assert submission.file_url == submission_dict["file_url"] != ""
    assert submission.thumbnail_url == submission_dict["thumbnail_url"] != ""
    assert submission.prev == submission_dict["prev"] == submission_test_data["prev"]
    assert submission.next == submission_dict["next"] == submission_test_data["next"]
    assert submission.favorite == submission_dict["favorite"] == submission_test_data["favorite"]
    assert bool(submission.favorite_toggle_link) == bool(submission_dict["favorite_toggle_link"]) == \
           bool(submission_test_data["favorite_toggle_link"])
    assert remove_user_icons(clean_html(submission.description)) == \
           remove_user_icons(clean_html(submission_dict["description"])) == \
           remove_user_icons(clean_html(submission_test_data["description"]))
    assert remove_user_icons(clean_html(submission.footer)) == \
           remove_user_icons(clean_html(submission_dict["footer"])) == \
           remove_user_icons(clean_html(submission_test_data["footer"]))
    assert submission.description_bbcode == submission_test_data["description_bbcode"]
    assert submission.footer_bbcode == submission_test_data["footer_bbcode"]

    assert file is not None and len(file) > 0

    assert len(faapi.comment.flatten_comments(submission.comments)) == submission.stats.comments

    comments: dict[int, Comment] = {c.id: c for c in faapi.comment.flatten_comments(submission.comments)}

    for comment in comments.values():
        assert comment.reply_to is None or isinstance(comment.reply_to, Comment)

        if comment.reply_to:
            assert comment.reply_to.id in comments
            assert comment in comments[comment.reply_to.id].replies

        if comment.replies:
            for reply in comment.replies:
                assert reply.reply_to == comment


# noinspection DuplicatedCode
def test_journal(cookies: RequestsCookieJar, journal_test_data: dict):
    api: FAAPI = FAAPI(cookies)

    journal = api.journal(journal_test_data["id"])
    journal_dict = dict(journal)

    assert journal.id == journal_dict["id"] == journal_test_data["id"]
    assert journal.title == journal_dict["title"] == journal_test_data["title"]
    assert journal.author.name.lower() == journal_dict["author"]["name"].lower() == journal_test_data["author"]["name"].lower()
    assert journal.author.join_date == journal_dict["author"]["join_date"] == \
           datetime.fromisoformat(journal_test_data["author"]["join_date"]) + dst_us()
    assert journal.author.avatar_url == journal_dict["author"]["avatar_url"] != ""
    assert journal.date == journal_dict["date"] == datetime.fromisoformat(journal_test_data["date"]) + dst_us()
    assert journal.stats.comments == journal_dict["stats"]["comments"] >= journal_test_data["stats"]["comments"]
    assert journal.mentions == journal_dict["mentions"] == journal_test_data["mentions"]
    assert remove_user_icons(clean_html(journal.content)) == \
           remove_user_icons(clean_html(journal_dict["content"])) == \
           remove_user_icons(clean_html(journal_test_data["content"]))
    assert remove_user_icons(clean_html(journal.header)) == \
           remove_user_icons(clean_html(journal_dict["header"])) == \
           remove_user_icons(clean_html(journal_test_data["header"]))
    assert remove_user_icons(clean_html(journal.footer)) == \
           remove_user_icons(clean_html(journal_dict["footer"])) == \
           remove_user_icons(clean_html(journal_test_data["footer"]))
    assert journal.content_bbcode == journal_test_data["content_bbcode"]
    assert journal.header_bbcode == journal_test_data["header_bbcode"]
    assert journal.footer_bbcode == journal_test_data["footer_bbcode"]

    assert len(faapi.comment.flatten_comments(journal.comments)) == journal.stats.comments

    comments: dict[int, Comment] = {c.id: c for c in faapi.comment.flatten_comments(journal.comments)}

    for comment in comments.values():
        assert comment.reply_to is None or isinstance(comment.reply_to, Comment)

        if comment.reply_to:
            assert comment.reply_to.id in comments
            assert comment in comments[comment.reply_to.id].replies

        if comment.replies:
            for reply in comment.replies:
                assert reply.reply_to == comment


# noinspection DuplicatedCode
def test_gallery(cookies: RequestsCookieJar, data: dict):
    api: FAAPI = FAAPI(cookies)

    ss: list[SubmissionPartial] = []
    p: Optional[int] = 1

    while p:
        ss_, p_ = api.gallery(data["gallery"]["user"], p)
        assert isinstance(ss, list)
        assert all(isinstance(s, SubmissionPartial) for s in ss_)
        assert p_ is None or isinstance(p_, int)
        assert p_ is None or p_ > p
        assert len(ss) or p == 1
        assert len(ss_) or p_ is None

        ss.extend(ss_)
        p = p_

    assert len(ss) >= data["gallery"]["length"]
    assert len({s.id for s in ss}) == len(ss)

    for submission in ss:
        assert submission.id > 0
        assert submission.type != ""
        assert submission.rating != ""
        assert submission.thumbnail_url != ""
        assert submission.author.name_url == username_url(data["gallery"]["user"])


# noinspection DuplicatedCode
def test_scraps(cookies: RequestsCookieJar, data: dict):
    api: FAAPI = FAAPI(cookies)

    ss: list[SubmissionPartial] = []
    p: Optional[int] = 1

    while p:
        ss_, p_ = api.scraps(data["scraps"]["user"], p)
        assert isinstance(ss, list)
        assert all(isinstance(s, SubmissionPartial) for s in ss_)
        assert p_ is None or isinstance(p_, int)
        assert p_ is None or p_ > p
        assert len(ss) or p == 1
        assert len(ss_) or p_ is None

        ss.extend(ss_)
        p = p_

    assert len(ss) >= data["scraps"]["length"]
    assert len({s.id for s in ss}) == len(ss)

    for submission in ss:
        assert submission.id > 0
        assert submission.type != ""
        assert submission.rating != ""
        assert submission.thumbnail_url != ""
        assert submission.author.name_url == username_url(data["scraps"]["user"])


# noinspection DuplicatedCode
def test_favorites(cookies: RequestsCookieJar, data: dict):
    api: FAAPI = FAAPI(cookies)

    ss: list[SubmissionPartial] = []
    p: Optional[str] = "/"

    while p and len(ss) < data["favorites"]["max_length"]:
        ss_, p_ = api.favorites(data["favorites"]["user"], p)
        assert isinstance(ss, list)
        assert all(isinstance(s, SubmissionPartial) for s in ss_)
        assert p_ is None or isinstance(p_, str)
        assert p_ is None or (p == "/" and p_ > p) or p_ < p
        assert len(ss) or p == "/"
        assert len(ss_) or p_ is None

        ss.extend(ss_)
        p = p_

    assert not data["favorites"]["next_page"] or p is not None
    assert len(ss) >= data["favorites"]["length"]
    assert len({s.id for s in ss}) == len(ss)

    for submission in ss:
        assert submission.id > 0
        assert submission.type != ""
        assert submission.rating != ""
        assert submission.thumbnail_url != ""


# noinspection DuplicatedCode
def test_journals(cookies: RequestsCookieJar, data: dict):
    api: FAAPI = FAAPI(cookies)

    js: list[JournalPartial] = []
    p: Optional[int] = 1

    while p:
        js_, p_ = api.journals(data["journals"]["user"], p)
        assert isinstance(js, list)
        assert all(isinstance(s, JournalPartial) for s in js_)
        assert p_ is None or isinstance(p_, int)
        assert p_ is None or p_ > p
        assert len(js) or p == 1
        assert len(js_) or p_ is None

        js.extend(js_)
        p = p_

    assert len(js) >= data["journals"]["length"]
    assert len({j.id for j in js}) == len(js)

    for journal in js:
        assert journal.id > 0
        assert journal.author.join_date.timestamp() > 0
        assert journal.date.timestamp() > 0
        assert journal.author.name_url == username_url(data["scraps"]["user"])


# noinspection DuplicatedCode
def test_watchlist_to(cookies: RequestsCookieJar, data: dict):
    api: FAAPI = FAAPI(cookies)
    assert api.login_status

    ws: list[UserPartial] = []
    p: Optional[int] = 1

    while p:
        ws_, p_ = api.watchlist_to(data["watchlist"]["user"], p)
        assert isinstance(ws, list)
        assert all(isinstance(s, UserPartial) for s in ws_)
        assert p_ is None or isinstance(p_, int)
        assert p_ is None or p_ > p
        assert len(ws) or p == 1
        assert len(ws_) or p_ is None

        ws.extend(ws_)
        p = p_

    assert len({w.name_url for w in ws}) == len(ws)


# noinspection DuplicatedCode
def test_watchlist_by(cookies: RequestsCookieJar, data: dict):
    api: FAAPI = FAAPI(cookies)
    assert api.login_status

    ws: list[UserPartial] = []
    p: Optional[int] = 1

    while p:
        ws_, p_ = api.watchlist_by(data["watchlist"]["user"], p)
        assert isinstance(ws, list)
        assert all(isinstance(s, UserPartial) for s in ws_)
        assert p_ is None or isinstance(p_, int)
        assert p_ is None or p_ > p
        assert len(ws) or p == 1
        assert len(ws_) or p_ is None

        ws.extend(ws_)
        p = p_

    assert len({w.name_url for w in ws}) == len(ws)
