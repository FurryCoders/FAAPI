from re import search as re_search
from time import perf_counter
from time import sleep
from typing import Any
from typing import Dict
from typing import List
from typing import Optional
from typing import Tuple
from typing import Union

from .connection import CloudflareScraper
from .connection import Response
from .connection import get
from .connection import get_binary_raw
from .connection import get_robots
from .connection import join_url
from .connection import make_session
from .parse import BeautifulSoup
from .parse import parse_page
from .sub import Sub
from .sub import SubPartial


class FAAPI:
    def __init__(self, cookies: List[Dict[str, Any]] = None):
        self.cookies: List[Dict[str, Any]] = [] if cookies is None else cookies
        self.session: CloudflareScraper = make_session(self.cookies)
        self.robots: Dict[str, List[str]] = get_robots()
        self.crawl_delay: float = float(self.robots["Crawl-delay"][0]) if self.robots.get("Crawl-delay", 0) else 1.0
        self.last_get: float = perf_counter() - self.crawl_delay
        self.raise_for_delay: bool = False

    def load_cookies(self, cookies: List[Dict[str, Any]]):
        self.cookies = cookies
        self.session = make_session(self.cookies)

    def handle_delay(self):
        if (delay_diff := perf_counter() - self.last_get) < self.crawl_delay:
            if self.raise_for_delay:
                raise Exception(f"Crawl-delay not respected {delay_diff}<{self.crawl_delay}")
            sleep(self.crawl_delay - delay_diff)
        self.last_get = perf_counter()

    def check_path(self, path: str):
        for pattern in self.robots.get("disallow", []):
            if re_search(pattern.replace("*", ".*"), "/" + path.lstrip("/")):
                raise Exception(f"Path {path} is not allowed by robots.txt {pattern}")

    def get(self, path: str, **params) -> Response:
        self.check_path(path)
        self.handle_delay()
        return get(self.session, path, **params)

    def get_parse(self, path: str, **params) -> Optional[BeautifulSoup]:
        res = self.get(path, **params)
        return parse_page(res.text) if res.ok else None

    def get_sub(self, sub_id: int, get_file: bool = False) -> Tuple[Sub, Optional[bytes]]:
        assert isinstance(sub_id, int) and sub_id > 0

        sub_page = self.get_parse(f"/view/{sub_id}")
        sub = Sub(sub_page)
        sub_file = self.get_sub_file(sub) if get_file else None

        return sub, sub_file

    def get_sub_file(self, sub: Sub) -> Optional[bytes]:
        self.handle_delay()
        return get_binary_raw(self.session, sub.file_url)

    def userpage(self, user: str) -> Tuple[str, str, Optional[BeautifulSoup]]:
        assert isinstance(user, str)

        page: Optional[BeautifulSoup] = self.get_parse(join_url("user", user))
        if page is None:
            return "", "", None

        username_div = page.find("div", class_="username")

        username = username_div.find("span").text.strip()
        status = username[0]
        username = username[1:]

        description = page.find("div", class_="userpage-profile").text.strip()

        return username, status, parse_page(description)

    def gallery(self, user: str, page: int = 1) -> Tuple[List[SubPartial], int]:
        assert isinstance(user, str)
        assert isinstance(page, int) and page >= 1

        page_parsed = self.get_parse(join_url("gallery", user, str(page)))

        if page_parsed is None or page_parsed.title.text.lower().startswith("account disabled"):
            return [], 0

        subs = page_parsed.findAll("figure")

        return list(map(SubPartial, subs)), (page + 1) if subs else 0

    def scraps(self, user: str, page: int = 1) -> Tuple[List[SubPartial], int]:
        assert isinstance(user, str)
        assert isinstance(page, int) and page >= 1

        page_parsed = self.get_parse(join_url("scraps", user, str(page)))

        if page_parsed is None or page_parsed.title.text.lower().startswith("account disabled"):
            return [], 0

        subs = page_parsed.findAll("figure")

        return list(map(SubPartial, subs)), (page + 1) if subs else 0

    def favorites(self, user: str, page: str = "") -> Tuple[List[SubPartial], str]:
        assert isinstance(user, str)
        assert isinstance(page, str)

        page_parsed = self.get_parse(join_url("favorites", user, page))

        if page_parsed is None or page_parsed.title.text.lower().startswith("account disabled"):
            return [], ""

        subs = page_parsed.findAll("figure")

        button_next = page_parsed.find("a", class_="button standard right")
        page_next: str = button_next["href"].split("/", 3)[-1] if button_next else ""

        return list(map(SubPartial, subs)), page_next

    def search(self, q: str, page: int = 1, **params) -> Tuple[List[SubPartial], int, int, int, int]:
        assert isinstance(q, str)
        assert isinstance(page, int)

        page_parsed = self.get_parse("search", q=q, page=page, **params)

        subs = page_parsed.findAll("figure")
        if page_parsed is None:
            return [], 0, 0, 0, 0

        query_stats = page_parsed.find("div", id="query-stats")
        for div in query_stats("div"):
            div.decompose()

        a, b, tot = map(int, re_search(r"(\d+)[^\d]*(\d+)[^\d]*(\d+)", query_stats.text.strip()).groups())
        page_next = (page + 1) if b < tot else 0

        return list(map(SubPartial, subs)), page_next, a, b, tot

    def user_exists(self, user: str):
        assert isinstance(user, str)

        res = self.get(join_url("view", user))

        if not res.ok:
            return False
        elif not (title := parse_page(res.text).title.text):
            return False
        elif title.text.lower() == "system error":
            return False
        elif title.text.lower().startswith("account disabled"):
            return False
        else:
            return True

    def sub_exists(self, sub_id: Union[int, str]):
        assert isinstance(sub_id, int) or (isinstance(sub_id, str) and sub_id.isdigit())

        res = self.get(join_url("view", str(sub_id)))

        if not res.ok:
            return False
        elif not (title := parse_page(res.text).title.text):
            return False
        elif title.text.lower() == "system error":
            return False
        else:
            return True
