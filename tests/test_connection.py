from os import environ
from platform import python_version
from platform import uname
from urllib.robotparser import RobotFileParser

import pytest
from requests import Response
from requests import Session
from requests.cookies import RequestsCookieJar

from faapi.__version__ import __version__
from faapi.connection import CloudflareScraper
from faapi.connection import get_robots
from faapi.connection import join_url
from faapi.connection import make_session
from faapi.connection import root
from faapi.exceptions import Unauthorized


@pytest.fixture
def cookies() -> RequestsCookieJar:
    jar: RequestsCookieJar = RequestsCookieJar()
    for name, value in map(lambda c: c.split("="), environ["TEST_COOKIES"].split(":")):
        jar.set(name, value)
    return jar


def test_make_session_cookie_jar():
    cookie_jar = RequestsCookieJar()
    cookie_jar.set("a", "a")
    result = make_session(cookie_jar)
    assert isinstance(result, CloudflareScraper)


def test_make_session_list_dict():
    result = make_session([{"name": "a", "value": "a"}])
    assert isinstance(result, CloudflareScraper)


def test_make_session_error():
    with pytest.raises(Unauthorized):
        make_session([])


def test_get_robots():
    with Session() as session:
        session.headers["User-Agent"] = \
            f"faapi/{__version__} Python/{python_version()} {(u := uname()).system}/{u.release} test"
        result = get_robots(session)
    assert isinstance(result, RobotFileParser)
    assert getattr(result, "default_entry", None) is not None


def test_get(cookies: RequestsCookieJar):
    res: Response = make_session(cookies).get(join_url(root, "view", 1))
    assert res.ok
