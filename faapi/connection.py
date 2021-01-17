from platform import python_version
from platform import uname
from time import sleep
from typing import Dict
from typing import List
from typing import Optional
from typing import Union

from cfscrape import CloudflareScraper
from cfscrape import create_scraper
from requests import Response
from requests import get as get_raw

from .__version__ import __version__

root = "https://www.furaffinity.net"
user_agent: str = f"faapi/{__version__} Python/{python_version()} {(u := uname()).system}/{u.release}"


def join_url(*url_comps: Union[str, int]) -> str:
    return "/".join(map(lambda e: str(e).strip(" /"), url_comps))


def ping():
    get_raw(root, headers={"User-Agent": user_agent}).raise_for_status()


def make_session(cookies: List[dict]) -> Optional[CloudflareScraper]:
    ping()

    cookies = [
        {"name": cookie["name"], "value": cookie["value"]}
        for cookie in cookies
        if "name" in cookie and "value" in cookie
    ]

    session: CloudflareScraper = create_scraper()

    for cookie in cookies:
        session.cookies.set(cookie["name"], cookie["value"])

    return session


def get_robots() -> Dict[str, List[str]]:
    res = get_raw(join_url(root, "robots.txt"), headers={"User-Agent": user_agent})

    if not res.ok:
        return {}

    robot: Dict[str, Union[int, str, List[str]]] = {}

    for elem in filter(lambda r: r not in ("", "#"), res.text.split("\n")):
        key, value = elem.split(":", 1)
        robot[key] = robot.get(key, []) + [value.strip()]

    return robot


def get(session: CloudflareScraper, path: str, **params) -> Response:
    return session.get(join_url(root, path), params=params, headers={"User-Agent": user_agent})


def get_binary_raw(session: CloudflareScraper, url: str, speed: Union[int, float] = 100) -> Optional[bytes]:
    assert isinstance(speed, int) or isinstance(speed, float)

    file_stream = session.get(url, stream=True, headers={"User-Agent": user_agent})

    if not file_stream.ok:
        file_stream.close()
        return None

    file_binary = bytes()
    for chunk in file_stream.iter_content(chunk_size=1024):
        file_binary += chunk
        sleep(1 / speed) if speed > 0 else None

    return file_binary
