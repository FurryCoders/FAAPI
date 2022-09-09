from http.cookiejar import CookieJar
from time import sleep
from time import time
from typing import Any
from typing import Optional
from typing import Union
from urllib.robotparser import RobotFileParser

from .connection import CloudflareScraper
from .connection import CookieDict
from .connection import Response
from .connection import get
from .connection import get_robots
from .connection import join_url
from .connection import make_session
from .connection import stream_binary
from .exceptions import DisallowedPath
from .exceptions import Unauthorized
from .journal import Journal
from .journal import JournalPartial
from .parse import BeautifulSoup
from .parse import check_page_raise
from .parse import parse_loggedin_user
from .parse import parse_page
from .parse import parse_submission_figures
from .parse import parse_user_favorites
from .parse import parse_user_journals
from .parse import parse_user_submissions
from .parse import parse_watchlist
from .parse import username_url
from .submission import Submission
from .submission import SubmissionPartial
from .user import User
from .user import UserPartial


# noinspection GrazieInspection
class FAAPI:
    """
    This class provides the methods to access and parse Fur Affinity pages and retrieve objects.
    """

    def __init__(self, cookies: Union[list[CookieDict], CookieJar]):
        """
        :param cookies: The cookies for the session.
        """

        self.session: CloudflareScraper = make_session(cookies)  # Session used for get requests
        self.robots: RobotFileParser = get_robots(self.session)  # robots.txt handler
        self.last_get: float = time() - self.crawl_delay  # Time of last get (UNIX time)
        self.raise_for_unauthorized: bool = True  # Control login checks
        self.timeout: Optional[int] = None  # Timeout for requests

    @property
    def user_agent(self) -> str:
        """
        The user agent of the session
        """
        return self.session.headers["User-Agent"]

    @property
    def crawl_delay(self) -> float:
        """
        Crawl delay from robots.txt
        """
        return float(self.robots.crawl_delay(self.user_agent) or 1)

    def load_cookies(self, cookies: Union[list[CookieDict], CookieJar]):
        """
        Load new cookies and create a new session.

        :param cookies: The cookies for the session.
        """
        self.session = make_session(cookies)

    def handle_delay(self):
        """
        Handles the crawl delay as set in the robots.txt
        """
        if (d := time() - self.last_get) < self.crawl_delay:
            sleep(self.crawl_delay - d)
        self.last_get = time()

    def check_path(self, path: str, *, raise_for_disallowed: bool = False) -> bool:
        """
        Checks whether a given path is allowed by the robots.txt.

        :param path: The path to check.
        :param raise_for_disallowed: Whether to raise an exception for a non-allowed path.
        :return: True if the path is allowed in the robots.txt, False otherwise.
        """
        if not (allowed := self.robots.can_fetch(self.user_agent, "/" + path.lstrip("/"))) and raise_for_disallowed:
            raise DisallowedPath(f"Path {path!r} is not allowed by robots.txt")
        return allowed

    @property
    def connection_status(self) -> bool:
        """
        Check the status of the connection to Fur Affinity.

        :return: True if it can connect, False otherwise.
        """
        try:
            return self.get("/").ok
        except ConnectionError:
            return False

    @property
    def login_status(self) -> bool:
        """
        Check the login status of the given cookies.

        :return: True if the cookies belong to a login session, False otherwise.
        """
        return parse_loggedin_user(self.get_parsed("login", skip_auth_check=True)) is not None

    def get(self, path: str, **params: Union[str, bytes, int, float]) -> Response:
        """
        Fetch a path with a GET request.
        The path is checked against the robots.txt before the request is made.
        The crawl-delay setting is enforced wth a wait time.

        :param path: The path to fetch.
        :param params: Query parameters for the request.
        :return: A Response object from the request.
        """
        self.check_path(path, raise_for_disallowed=True)
        self.handle_delay()
        return get(self.session, path, timeout=self.timeout, params=params)

    def get_parsed(self, path: str, *, skip_page_check: bool = False, skip_auth_check: bool = False,
                   **params: Union[str, bytes, int, float]) -> BeautifulSoup:
        """
        Fetch a path with a GET request and parse it using BeautifulSoup.

        :param path: The path to fetch.
        :param skip_page_check: Whether to skip checking the parsed page for errors.
        :param skip_auth_check: Whether to skip checking the parsed page for login status.
        :param params: Query parameters for the request.
        :return: A BeautifulSoup object containing the parsed content of the request response.
        """
        response: Response = self.get(path, **params)
        response.raise_for_status()
        page: BeautifulSoup = parse_page(response.text)
        if not skip_page_check:
            check_page_raise(page)
        if not skip_auth_check and self.raise_for_unauthorized and not parse_loggedin_user(page):
            raise Unauthorized("Not logged in")
        return page

    def me(self) -> Optional[User]:
        """
        Fetch the information of the logged-in user.

        :return: A User object for the logged-in user, or None if the cookies are not from a login session.
        """
        return self.user(user) if (user := parse_loggedin_user(self.get_parsed("login"))) else None

    def frontpage(self) -> list[SubmissionPartial]:
        """
        Fetch latest submissions from Fur Affinity's front page

        :return: A list of SubmissionPartial objects
        """
        page_parsed: BeautifulSoup = self.get_parsed("/")
        submissions: list[SubmissionPartial] = [SubmissionPartial(f) for f in parse_submission_figures(page_parsed)]
        return sorted({s for s in submissions}, reverse=True)

    def submission(self, submission_id: int, get_file: bool = False, *, chunk_size: int = None
                   ) -> tuple[Submission, Optional[bytes]]:
        """
        Fetch a submission and, optionally, its file.

        :param submission_id: The ID of the submission.
        :param get_file: Whether to download the submission file.
        :param chunk_size: The chunk_size to be used for the download (does not override get_file).
        :return: A Submission object and a bytes object (if the submission file is downloaded).
        """
        sub: Submission = Submission(self.get_parsed(join_url("view", int(submission_id))))
        sub_file: Optional[bytes] = self.submission_file(sub, chunk_size=chunk_size) if get_file and sub.id else None
        return sub, sub_file

    def submission_file(self, submission: Submission, *, chunk_size: int = None) -> bytes:
        """
        Fetch a submission file from a Submission object.

        :param submission: A Submission object.
        :param chunk_size: The chunk_size to be used for the download.
        :return: The submission file as a bytes object.
        """
        self.handle_delay()
        return stream_binary(self.session, submission.file_url, chunk_size=chunk_size, timeout=self.timeout)

    def journal(self, journal_id: int) -> Journal:
        """
        Fetch a journal.

        :param journal_id: The ID of the journal.
        :return: A Journal object.
        """
        return Journal(self.get_parsed(join_url("journal", int(journal_id))))

    def user(self, user: str) -> User:
        """
        Fetch a user.

        :param user: The name of the user (_ characters are allowed).
        :return: A User object.
        """
        return User(self.get_parsed(join_url("user", username_url(user))))

    # noinspection DuplicatedCode
    def gallery(self, user: str, page: int = 1) -> tuple[list[SubmissionPartial], Optional[int]]:
        """
        Fetch a user's gallery page.

        :param user: The name of the user (_ characters are allowed).
        :param page: The page to fetch.
        :return: A list of SubmissionPartial objects and the next page (None if it is the last).
        """
        page_parsed: BeautifulSoup = self.get_parsed(join_url("gallery", username_url(user), int(page)))
        info_parsed: dict[str, Any] = parse_user_submissions(page_parsed)
        author: UserPartial = UserPartial()
        author.name, author.status, author.title, author.join_date, author.user_icon_url = [
            info_parsed["user_name"], info_parsed["user_status"],
            info_parsed["user_title"], info_parsed["user_join_date"],
            info_parsed["user_icon_url"]
        ]
        for s in (submissions := list(map(SubmissionPartial, info_parsed["figures"]))):
            s.author = author
        return submissions, (page + 1) if not info_parsed["last_page"] else None

    # noinspection DuplicatedCode
    def scraps(self, user: str, page: int = 1) -> tuple[list[SubmissionPartial], Optional[int]]:
        """
        Fetch a user's scraps page.

        :param user: The name of the user (_ characters are allowed).
        :param page: The page to fetch.
        :return: A list of SubmissionPartial objects and the next page (None if it is the last).
        """
        page_parsed: BeautifulSoup = self.get_parsed(join_url("scraps", username_url(user), int(page)))
        info_parsed: dict[str, Any] = parse_user_submissions(page_parsed)
        author: UserPartial = UserPartial()
        author.name, author.status, author.title, author.join_date, author.user_icon_url = [
            info_parsed["user_name"], info_parsed["user_status"],
            info_parsed["user_title"], info_parsed["user_join_date"],
            info_parsed["user_icon_url"]
        ]
        for s in (submissions := list(map(SubmissionPartial, info_parsed["figures"]))):
            s.author = author
        return submissions, (page + 1) if not info_parsed["last_page"] else None

    def favorites(self, user: str, page: str = "") -> tuple[list[SubmissionPartial], Optional[str]]:
        """
        Fetch a user's favorites page.

        :param user: The name of the user (_ characters are allowed).
        :param page: The page to fetch.
        :return: A list of SubmissionPartial objects and the next page (None if it is the last).
        """
        page_parsed: BeautifulSoup = self.get_parsed(join_url("favorites", username_url(user), page.strip()))
        info_parsed: dict[str, Any] = parse_user_favorites(page_parsed)
        submissions: list[SubmissionPartial] = list(map(SubmissionPartial, info_parsed["figures"]))
        return submissions, info_parsed["next_page"] or None

    def journals(self, user: str, page: int = 1) -> tuple[list[JournalPartial], Optional[int]]:
        """
        Fetch a user's journals page.

        :param user: The name of the user (_ characters are allowed).
        :param page: The page to fetch.
        :return: A list of Journal objects and the next page (None if it is the last).
        """
        page_parsed: BeautifulSoup = self.get_parsed(join_url("journals", username_url(user), int(page)))
        info_parsed: dict[str, Any] = parse_user_journals(page_parsed)
        author: UserPartial = UserPartial()
        author.name, author.status, author.title, author.join_date, author.user_icon_url = [
            info_parsed["user_name"], info_parsed["user_status"],
            info_parsed["user_title"], info_parsed["user_join_date"],
            info_parsed["user_icon_url"]
        ]
        for j in (journals := list(map(JournalPartial, info_parsed["sections"]))):
            j.author = author
        return journals, (page + 1) if not info_parsed["last_page"] else None

    def watchlist_to(self, user: str, page: int = 1) -> tuple[list[UserPartial], Optional[int]]:
        """
        Fetch a page from the list of users watching the user.

        :param user: The name of the user (_ characters are allowed).
        :param page: The page to fetch.
        :return: A list of UserPartial objects and the next page (None if it is the last).
        """
        users: list[UserPartial] = []
        us, np = parse_watchlist(
            self.get_parsed(join_url("watchlist", "to", username_url(user), page), skip_auth_check=True))
        for s, u in us:
            _user: UserPartial = UserPartial()
            _user.name = u
            _user.status = s
            users.append(_user)
        return users, np if np and np != page else None

    def watchlist_by(self, user: str, page: int = 1) -> tuple[list[UserPartial], Optional[int]]:
        """
        Fetch a page from the list of users watched by the user.
        :param user: The name of the user (_ characters are allowed).
        :param page: The page to fetch.
        :return: A list of UserPartial objects and the next page (None if it is the last).
        """
        users: list[UserPartial] = []
        us, np = parse_watchlist(
            self.get_parsed(join_url("watchlist", "by", username_url(user), page), skip_auth_check=True))
        for s, u in us:
            _user: UserPartial = UserPartial()
            _user.name = u
            _user.status = s
            users.append(_user)
        return users, np if np and np != page else None
