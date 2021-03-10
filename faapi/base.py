from re import search as re_search
from time import perf_counter
from time import sleep
from typing import Any
from typing import Dict
from typing import List
from typing import Optional
from typing import Tuple

from .connection import CloudflareScraper
from .connection import Response
from .connection import get
from .connection import get_binary_raw
from .connection import get_robots
from .connection import join_url
from .connection import make_session
from .exceptions import CrawlDelayError
from .exceptions import DisallowedPath
from .journal import Journal
from .parse import BeautifulSoup
from .parse import Tag
from .parse import check_page
from .parse import check_page_raise
from .parse import parse_page
from .parse import parse_watchlist
from .submission import Submission
from .submission import SubmissionPartial
from .user import User


class FAAPI:
    def __init__(self, cookies: List[Dict[str, Any]] = None):
        self.cookies: List[Dict[str, Any]] = [] if cookies is None else cookies
        self.session: CloudflareScraper = make_session(self.cookies)
        self.robots: Dict[str, List[str]] = get_robots()
        self.crawl_delay: float = float(self.robots.get("Crawl-delay", [1.0])[0])
        self.last_get: float = perf_counter() - self.crawl_delay
        self.raise_for_delay: bool = False

    def load_cookies(self, cookies: List[Dict[str, Any]]):
        self.cookies = cookies
        self.session = make_session(self.cookies)

    def handle_delay(self):
        if (delay_diff := perf_counter() - self.last_get) < self.crawl_delay:
            if self.raise_for_delay:
                raise CrawlDelayError(f"Crawl-delay not respected {delay_diff}<{self.crawl_delay}")
            sleep(self.crawl_delay - delay_diff)
        self.last_get = perf_counter()

    def check_path(self, path: str):
        for pattern in self.robots.get("disallow", []):
            if re_search(fr"^{pattern.replace('*', '.*')}", "/" + path.lstrip("/")):
                raise DisallowedPath(f"Path {path} is not allowed by robots.txt {pattern}")

    @property
    def connection_status(self) -> bool:
        try:
            return self.get("/").ok
        except ConnectionError:
            return False

    def get(self, path: str, **params) -> Response:
        self.check_path(path)
        self.handle_delay()
        return get(self.session, path, **params)

    def get_parse(self, path: str, **params) -> Optional[BeautifulSoup]:
        response: Response = self.get(path, **params)
        response.raise_for_status()
        return parse_page(response.text) if response.ok else None

    def get_submission(self, submission_id: int, get_file: bool = False) -> Tuple[Submission, Optional[bytes]]:
        sub: Submission = Submission(self.get_parse(join_url("view", int(submission_id))))
        sub_file: Optional[bytes] = self.get_submission_file(sub) if get_file and sub.id else None
        return sub, sub_file

    def get_submission_file(self, submission: Submission) -> Optional[bytes]:
        self.handle_delay()
        return get_binary_raw(self.session, submission.file_url)

    def get_journal(self, journal_id: int) -> Journal:
        return Journal(self.get_parse(join_url("journal", int(journal_id))))

    def get_user(self, user: str) -> User:
        return User(self.get_parse(join_url("user", user)))

    def gallery(self, user: str, page: int = 1) -> Tuple[List[SubmissionPartial], int]:
        check_page_raise(page_parsed := self.get_parse(join_url("gallery", user, int(page))))
        return list(map(SubmissionPartial, s := page_parsed.select("figure[id^='sid-']"))), (page + 1) if s else 0

    def scraps(self, user: str, page: int = 1) -> Tuple[List[SubmissionPartial], int]:
        check_page_raise(page_parsed := self.get_parse(join_url("scraps", user, int(page))))
        return list(map(SubmissionPartial, s := page_parsed.select("figure[id^='sid-']"))), (page + 1) if s else 0

    def favorites(self, user: str, page: str = "") -> Tuple[List[SubmissionPartial], str]:
        check_page_raise(page_parsed := self.get_parse(join_url("favorites", user, page.strip())))
        tag_next: Optional[Tag] = page_parsed.select_one("a[class~=button][class~=standard][class~=right]")
        next_page: str = tag_next["href"].split("/", 3)[-1] if tag_next else ""
        return list(map(SubmissionPartial, page_parsed.select("figure[id^='sid-']"))), next_page

    def journals(self, user: str, page: int = 1) -> Tuple[List[Journal], int]:
        check_page_raise(page_parsed := self.get_parse(join_url("journals", user, int(page))))
        username: str = page_parsed.select_one("div[class~=username] span").text.strip()[1:]
        journals: List[Journal] = list(map(Journal, page_parsed.select("section[id^='jid:']")))
        for j in journals:
            j.author = username
        return journals, (page + 1) if journals else 0

    def search(self, q: str, page: int = 1, **params) -> Tuple[List[SubmissionPartial], int, int, int, int]:
        check_page_raise(page_parsed := self.get_parse("search", q=q, page=(page := int(page)), **params))
        tag_stats: Tag = page_parsed.select_one("div[id='query-stats']")
        for div in tag_stats.select("div"):
            div.decompose()
        a, b, tot = map(int, re_search(r"(\d+)[^\d]*(\d+)[^\d]*(\d+)", tag_stats.text.strip()).groups())
        next_page: int = (page + 1) if b < tot else 0
        return list(map(SubmissionPartial, page_parsed.select("figure[id^='sid-']"))), next_page, a - 1, b - 1, tot

    def watchlist_to(self, user: str) -> List[User]:
        users: List[User] = []
        for s, u in parse_watchlist(self.get_parse(join_url("watchlist", "to", user))):
            user: User = User()
            user.name = u
            user.status = s
            users.append(user)
        return users

    def watchlist_by(self, user: str) -> List[User]:
        users: List[User] = []
        for s, u in parse_watchlist(self.get_parse(join_url("watchlist", "by", user))):
            user: User = User()
            user.name = u
            user.status = s
            users.append(user)
        return users

    def user_exists(self, user: str) -> int:
        """
        0 okay
        1 account disabled
        2 system error
        3 unknown error
        4 request error
        """

        if not (res := self.get(join_url("user", user))).ok:
            return 4
        elif (check := check_page(parse_page(res.text))) == 0:
            return 0
        elif check == 3:
            return 1
        elif check == 4:
            return 2
        else:
            return 3

    def submission_exists(self, submission_id: int) -> int:
        """
        0 okay
        1 account disabled
        2 system error
        3 unknown error
        4 request error
        """

        if not (res := self.get(join_url("view", submission_id))).ok:
            return 4
        elif (check := check_page(parse_page(res.text))) == 0:
            return 0
        elif check == 3:
            return 1
        elif check == 4:
            return 2
        else:
            return 3

    def journal_exists(self, journal_id: int) -> int:
        """
        0 okay
        1 account disabled
        2 system error
        3 unknown error
        4 request error
        """

        if not (res := self.get(join_url("journal", journal_id))).ok:
            return 4
        elif (check := check_page(parse_page(res.text))) == 0:
            return 0
        elif check == 3:
            return 1
        elif check == 4:
            return 2
        else:
            return 3
