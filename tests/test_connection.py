from json import load
from pathlib import Path
from urllib.robotparser import RobotFileParser

from pytest import fixture
from pytest import raises
from requests import Response, Session
from requests.cookies import RequestsCookieJar

from faapi.connection import get_robots
from faapi.connection import join_url
from faapi.connection import make_session
from faapi.connection import root
from faapi.exceptions import Unauthorized

__root__: Path = Path(__file__).resolve().parent


@fixture
def data() -> dict:
    return load((__root__ / "test_data.json").open())


@fixture
def cookies(data: dict) -> RequestsCookieJar:
    return data["cookies"]


def test_make_session_cookie_jar():
    cookie_jar = RequestsCookieJar()
    cookie_jar.set("a", "a")
    result = make_session(cookie_jar, Session)
    assert isinstance(result, Session)


def test_make_session_list_dict():
    result = make_session([{"name": "a", "value": "a"}], Session)
    assert isinstance(result, Session)


def test_make_session_error():
    with raises(Unauthorized):
        make_session([], Session)


def test_get_robots(cookies: RequestsCookieJar):
    result = get_robots(make_session(cookies, Session))
    assert isinstance(result, RobotFileParser)
    assert getattr(result, "default_entry", None) is not None


def test_get(cookies: RequestsCookieJar):
    res: Response = make_session(cookies, Session).get(join_url(root, "view", 1))
    assert res.ok
