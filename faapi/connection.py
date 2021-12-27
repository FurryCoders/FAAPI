from http.cookiejar import Cookie
from http.cookiejar import CookieJar
from platform import python_version
from platform import uname
from time import sleep
from typing import Optional
from typing import Union

from cfscrape import CloudflareScraper
from cfscrape import create_scraper
from requests import Response
from requests import get as get_raw
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


def get_robots() -> dict[str, list[str]]:
    res: Response = get_raw(join_url(root, "robots.txt"), headers={"User-Agent": user_agent})

    res.raise_for_status()

    robot: dict[str, Union[int, str, list[str]]] = {}

    for elem in filter(lambda r: r not in ("", "#"), res.text.split("\n")):
        key, value = elem.split(":", 1)
        robot[key] = [*robot.get(key, []), value.strip()]

    return robot


def get(session: CloudflareScraper, path: str, **params) -> Response:
    return session.get(join_url(root, path), params=params)


def stream_binary(session: CloudflareScraper, url: str, *, chunk_size: Optional[int] = None) -> bytes:
    stream: Response = session.get(url, stream=chunk_size is not None)
    stream.raise_for_status()

    file_binary: bytes = bytes().join(stream.iter_content(chunk_size=chunk_size)) if chunk_size else stream.content

    if (length := int(stream.headers.get("Content-Length", 0))) > 0 and length != len(file_binary):
        raise IncompleteRead(l := len(file_binary), length - l)

    return file_binary
