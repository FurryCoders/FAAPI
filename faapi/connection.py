from http.client import IncompleteRead
from http.cookiejar import Cookie
from http.cookiejar import CookieJar
from platform import python_version
from platform import uname
from re import compile as re_compile
from typing import Optional
from typing import Union
from urllib.robotparser import RobotFileParser

from cfscrape import CloudflareScraper  # type: ignore
from cfscrape import create_scraper  # type: ignore
from requests import Response
from requests import Session

from .__version__ import __version__
from .exceptions import Unauthorized
from .exceptions import _raise_exception

root: str = "https://www.furaffinity.net"


def join_url(*url_comps: Union[str, int]) -> str:
    return "/".join(map(lambda e: str(e).strip(" /"), url_comps))


def make_session(cookies: Union[list[dict[str, str]], CookieJar]) -> CloudflareScraper:
    assert len(cookies), _raise_exception(Unauthorized("No cookies for session"))
    session: CloudflareScraper = create_scraper()
    session.headers["User-Agent"] = f"faapi/{__version__} Python/{python_version()} {(u := uname()).system}/{u.release}"

    for cookie in cookies:
        if isinstance(cookie, Cookie):
            session.cookies.set(cookie.name, cookie.value)
        else:
            session.cookies.set(cookie["name"], cookie["value"])

    return session


def get_robots(session: Session) -> RobotFileParser:
    robots: RobotFileParser = RobotFileParser(url := join_url(root, "robots.txt"))
    robots.parse(filter(re_compile(r"^[^#].*").match, session.get(url).text.splitlines()))
    return robots


def get(session: CloudflareScraper, path: str, **params) -> Response:
    return session.get(join_url(root, path), params=params)


def stream_binary(session: CloudflareScraper, url: str, *, chunk_size: Optional[int] = None) -> bytes:
    stream: Response = session.get(url, stream=True)
    stream.raise_for_status()

    file_binary: bytes = bytes().join(stream.iter_content(chunk_size))

    if (length := int(stream.headers.get("Content-Length", 0))) > 0 and length != len(file_binary):
        raise IncompleteRead(file_binary, length - len(file_binary))

    return file_binary
