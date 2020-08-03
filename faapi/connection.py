from time import sleep
from typing import Dict
from typing import List
from typing import Optional
from typing import Union

from cfscrape import CloudflareScraper
from cfscrape import create_scraper
from requests import Response
from requests import get as get_raw
from requests.exceptions import ConnectTimeout
from requests.exceptions import ConnectionError

root = "https://www.furaffinity.net"


def join_url(*url_comps: str) -> str:
    return "/".join(map(lambda e: e.strip(" /"), url_comps))


def ping() -> bool:
    try:
        return get_raw(root).ok
    except (ConnectionError, ConnectTimeout):
        return False


def make_session(cookies: List[dict]) -> Optional[CloudflareScraper]:
    if not ping():
        return None

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
    res = get_raw(join_url(root, "robots.txt"))

    if not res.ok:
        return {}

    robot: Dict[str, Union[int, str, List[str]]] = {}

    for elem in filter(lambda r: r not in ("", "#"), res.text.split("\n")):
        key, value = elem.split(":", 1)
        robot[key] = robot.get(key, []) + [value.strip()]

    return robot


def get(session: CloudflareScraper, path: str, **params) -> Response:
    return session.get(join_url(root, path), params=params)


def get_binary_raw(session: CloudflareScraper, url: str, speed: Union[int, float] = 100) -> Optional[bytes]:
    assert isinstance(speed, int) or isinstance(speed, float)

    file_stream = session.get(url, stream=True)

    if not file_stream.ok:
        file_stream.close()
        return None

    file_binary = bytes()
    for chunk in file_stream.iter_content(chunk_size=1024):
        file_binary += chunk
        sleep(1 / speed) if speed > 0 else None

    return file_binary
