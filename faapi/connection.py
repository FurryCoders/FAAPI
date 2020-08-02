from json import load as json_load
from os.path import isfile
from typing import Dict
from typing import List
from typing import Optional
from typing import Tuple
from typing import Union

from cfscrape import CloudflareScraper
from cfscrape import create_scraper
from requests import Response
from requests import get as get_raw
from requests.exceptions import ConnectTimeout
from requests.exceptions import ConnectionError

root = "https://www.furaffinity.net"


def join_url(*url_comps: str) -> str:
    return '/'.join(map(lambda e: e.strip(" /"), url_comps))


def ping() -> bool:
    try:
        return get_raw(root).ok
    except (ConnectionError, ConnectTimeout):
        return False


def cookies_load(cookies_file: str = "", cookies_list: List[dict] = None) -> List[dict]:
    cookies_list = [] if cookies_list is None else cookies_list

    assert isinstance(cookies_file, str)
    assert isinstance(cookies_list, list)
    assert all(isinstance(cookie, dict) for cookie in cookies_list)

    if cookies_file and isfile(cookies_file):
        with open(cookies_file, "r") as f:
            cookies_list = json_load(f)
        assert isinstance(cookies_list, list)

    return cookies_list


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


def get_robots() -> Dict[str, Union[str, List[str]]]:
    res = get_raw(join_url(root, "robots.txt"))

    if not res.ok:
        return {}

    robot: Dict[str, Union[int, str, List[str]]] = {}

    for elem in filter(lambda r: r not in ("", "#"), res.text.split()):
        key, value = elem.split(":", 1)
        robot[key] = robot.get(key, []) + [value.strip()]

    return robot


def get(session: CloudflareScraper, path: str) -> Tuple[int, Response]:
    res = session.get(join_url(root, path))
    return res.status_code, res
