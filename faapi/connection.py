from http.cookiejar import Cookie
from http.cookiejar import CookieJar
from platform import python_version
from platform import uname
from re import sub
from typing import Optional
from typing import Union
from urllib.robotparser import RobotFileParser

from cfscrape import CloudflareScraper
from cfscrape import create_scraper
from requests import Response
from requests import Session
from urllib3.exceptions import IncompleteRead

from .__version__ import __version__

root: str = "https://www.furaffinity.net"
user_agent: str = f"faapi/{__version__} Python/{python_version()} {(u := uname()).system}/{u.release}"


def join_url(*url_comps: Union[str, int]) -> str:
    return "/".join(map(lambda e: str(e).strip(" /"), url_comps))


def make_session(cookies: Union[list[dict[str, str]], CookieJar]) -> CloudflareScraper:
    session: CloudflareScraper = create_scraper()
    session.headers["User-Agent"] = user_agent

    for cookie in cookies:
        if isinstance(cookie, Cookie):
            session.cookies.set(cookie.name, cookie.value, )
        else:
            session.cookies.set(cookie["name"], cookie["value"])

    return session


def get_robots(session: Session) -> RobotFileParser:
    robots: RobotFileParser = RobotFileParser(url := join_url(root, "robots.txt"))
    robots.parse([sub(r"^([^:\s]+:)", lambda m: m[1][0].upper() + m[1][1:], line)
                  for line in sub(r"\n[#\n]+", "\n", session.get(url).text).splitlines()])
    return robots


def get(session: CloudflareScraper, path: str, **params) -> Response:
    return session.get(join_url(root, path), params=params)


def stream_binary(session: CloudflareScraper, url: str, *, chunk_size: Optional[int] = None) -> bytes:
    stream: Response = session.get(url, stream=chunk_size is not None)
    stream.raise_for_status()

    file_binary: bytes = bytes().join(stream.iter_content(chunk_size=chunk_size)) if chunk_size else stream.content

    if (length := int(stream.headers.get("Content-Length", 0))) > 0 and length != len(file_binary):
        raise IncompleteRead(l := len(file_binary), length - l)

    return file_binary
