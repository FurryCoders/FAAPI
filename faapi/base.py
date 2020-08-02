from re import search as re_search
from typing import List
from typing import Optional
from typing import Tuple
from typing import Union

from .connection import cookies_load
from .connection import get
from .connection import join_url
from .connection import make_session, get_binary_raw
from .parse import BeautifulSoup
from .parse import page_parse
from .parse import sub_parse_figure
from .sub import FASub


class FAAPI:
    def __init__(self, cookies_f: str = "", cookies_l: List[dict] = None):
        cookies_l = [] if cookies_l is None else cookies_l

        self.session = make_session(cookies_load(cookies_f, cookies_l))

    def get(self, url: str, **params):
        return get(self.session, url, **params)

    def get_parse(self, url: str, **params) -> Optional[BeautifulSoup]:
        res = get(self.session, url, **params)
        return page_parse(res.text) if res.ok else None

    def get_sub(self, sub_id: Union[int, str], get_file: bool = False) -> Tuple[FASub, Optional[bytes]]:
        assert isinstance(sub_id, int) or (isinstance(sub_id, str) and sub_id.isdigit())

        sub_page = self.get_parse(f"/view/{sub_id}")
        sub = FASub(sub_page)
        sub_file = get_binary_raw(self.session, sub.file_url) if get_file else None

        return sub, sub_file

    def userpage(self, user: str) -> Tuple[str, str, str]:
        assert isinstance(user, str)

        page: Optional[BeautifulSoup] = self.get_parse(join_url("user", user))
        if page is None:
            return "", "", ""

        username_div = page.find(name="div", attrs={"class": "username"})

        username = username_div.find("span").text.strip()
        status = username[0]
        username = username[1:]

        description = page.find(name="div", attrs={"class": "userpage-profile"}).text.strip()

        return username, status, description

    def gallery(self, user: str, page: int = 1) -> Tuple[List[dict], int]:
        assert isinstance(user, str)
        assert isinstance(page, int) and page >= 1

        page_parsed = self.get_parse(join_url("gallery", user, str(page)))

        if page_parsed is None or page_parsed.title.text.lower().startswith("account disabled"):
            return [], 0

        subs = page_parsed.findAll(name="figure")

        return list(map(sub_parse_figure, subs)), page + 1

    def scraps(self, user: str, page: int = 1) -> Tuple[List[dict], int]:
        assert isinstance(user, str)
        assert isinstance(page, int) and page >= 1

        page_parsed = self.get_parse(join_url("scraps", user, str(page)))

        if page_parsed is None or page_parsed.title.text.lower().startswith("account disabled"):
            return [], 0

        subs = page_parsed.findAll(name="figure")

        return list(map(sub_parse_figure, subs)), page + 1

    def favorites(self, user: str, page: str = "") -> Tuple[List[dict], str]:
        assert isinstance(user, str)
        assert isinstance(page, str)

        page_parsed = self.get_parse(join_url("favorites", user, page))

        if page_parsed is None or page_parsed.title.text.lower().startswith("account disabled"):
            return [], ""

        subs = page_parsed.findAll(name="figure")

        button_next = page_parsed.find(name="a", limit=1, attrs={"class": "button standard right"})
        page_next: str = button_next["href"].split("/", 3)[-1]

        return list(map(sub_parse_figure, subs)), page_next

    def search(self, **params) -> Tuple[List[dict], int, int, int, int]:
        assert "q" in params

        page_parsed = self.get_parse("search", **params)

        subs = page_parsed.find(name="figure")
        if page_parsed is None:
            return [], 0, 0, 0, 0

        query_stats = page_parsed.find("div", id="query-stats")
        for div in query_stats("div"):
            div.decompose()

        a, b, tot = re_search(r"(\d+)[^\d]*(\d+)[^\d]*(\d+)", query_stats.text.strip()).groups()
        page_next = (params.get("page", 1) + 1) if b < tot else 0

        return list(map(sub_parse_figure, subs)), page_next, a, b, tot

    def user_exists(self, user: str):
        assert isinstance(user, str)

        page_parsed = self.get_parse(f"/user/{user}/")
        title = page_parsed.title.text

        if not title:
            return False
        elif title.text.lower() == "system error":
            return False
        elif title.text.lower().startswith("account disabled"):
            return False
        else:
            return True

    def sub_exists(self, sub_id: Union[int, str]):
        assert isinstance(sub_id, int) or (isinstance(sub_id, str) and sub_id.isdigit())

        page_parsed = self.get_parse(f"/view/{sub_id}/")
        title = page_parsed.title.text

        if not title:
            return False
        elif title.text.lower() == "system error":
            return False
        else:
            return True
