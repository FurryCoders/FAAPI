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
from urllib3.exceptions import IncompleteRead

from .__version__ import __version__

root: str = "https://www.furaffinity.net"
user_agent: str = f"faapi/{__version__} Python/{python_version()} {(u := uname()).system}/{u.release}"


def join_url(*url_comps: Union[str, int]) -> str:
    return "/".join(map(lambda e: str(e).strip(" /"), url_comps))


def ping():
    get_raw(root, headers={"User-Agent": user_agent}).raise_for_status()


def make_session(cookies: List[dict]) -> Optional[CloudflareScraper]:
    ping()

    cookies: List[Dict[str, str]] = [
        {"name": cookie["name"], "value": cookie["value"]}
        for cookie in cookies
        if "name" in cookie and "value" in cookie
    ]

    session: CloudflareScraper = create_scraper()

    for cookie in cookies:
        session.cookies.set(cookie["name"], cookie["value"])

    return session


def get_robots() -> Dict[str, List[str]]:
    res: Response = get_raw(join_url(root, "robots.txt"), headers={"User-Agent": user_agent})

    res.raise_for_status()

    robot: Dict[str, Union[int, str, List[str]]] = {}

    for elem in filter(lambda r: r not in ("", "#"), res.text.split("\n")):
        key, value = elem.split(":", 1)
        robot[key] = [*robot.get(key, []), value.strip()]

    return robot


def get(session: CloudflareScraper, path: str, **params) -> Response:
    return session.get(join_url(root, path), params=params, headers={"User-Agent": user_agent})


def get_binary_raw(session: CloudflareScraper, url: str, speed: Union[int, float] = 100) -> Optional[bytes]:
    assert isinstance(speed, int) or isinstance(speed, float)

    file_stream: Response = session.get(url, stream=True, headers={"User-Agent": user_agent})

    file_stream.raise_for_status()

    file_binary: bytes = bytes()
    for chunk in file_stream.iter_content(chunk_size=1024):
        file_binary += chunk
        sleep(1 / speed) if speed > 0 else None

    if (length := int(file_stream.headers.get("Content-Length", 0))) > 0 and length != len(file_binary):
        raise IncompleteRead(l := len(file_binary), length - l)

    return file_binary
