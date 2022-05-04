from collections import namedtuple
from datetime import datetime
from typing import Optional

from .connection import join_url
from .connection import root
from .exceptions import _raise_exception
from .parse import BeautifulSoup
from .parse import Tag
from .parse import check_page_raise
from .parse import parse_user_page
from .parse import parse_user_tag
from .parse import username_url


class UserStats(namedtuple("UserStats", ["views", "submissions", "favorites", "comments_earned",
                                         "comments_made", "journals", "watched_by", "watching"])):
    """
    This object contains a user's statistics:
    * views
    * submissions
    * favorites
    * comments_earned
    * comments_made
    * journals
    * watched_by
    * watching
    """


class UserBase:
    """
    Base class for the user objects.
    """

    def __init__(self):
        self.name: str = ""
        self.status: str = ""

    def __eq__(self, other) -> bool:
        if isinstance(other, UserBase):
            return other.name_url == self.name_url
        elif isinstance(other, str):
            return username_url(other) == self.name_url
        return False

    def __gt__(self, other) -> bool:
        if isinstance(other, UserBase):
            return self.name_url > other.name_url
        elif isinstance(other, str):
            return self.name_url > username_url(other)
        return False

    def __ge__(self, other) -> bool:
        if isinstance(other, UserBase):
            return self.name_url >= other.name_url
        elif isinstance(other, str):
            return self.name_url >= username_url(other)
        return False

    def __lt__(self, other) -> bool:
        if isinstance(other, UserBase):
            return self.name_url < other.name_url
        elif isinstance(other, str):
            return self.name_url < username_url(other)
        return False

    def __le__(self, other) -> bool:
        if isinstance(other, UserBase):
            return self.name_url <= other.name_url
        elif isinstance(other, str):
            return self.name_url <= username_url(other)
        return False

    def __iter__(self):
        yield "name", self.name
        yield "status", self.status

    def __repr__(self):
        return self.__str__()

    def __str__(self):
        return self.status + self.name

    @property
    def name_url(self):
        """
        Compose the URL-safe username.

        :return: The cleaned username.
        """
        return username_url(self.name)

    @property
    def url(self):
        """
        Compose the full URL to the user.

        :return: The URL to the user.
        """
        return join_url(root, "user", self.name_url)


class UserPartial(UserBase):
    """
    Contains partial user information gathered from user folders (gallery, journals, etc.) and submission/journal pages.
    """

    def __init__(self, user_tag: Tag = None):
        """
        :param user_tag: The tag from which to parse the user information.
        """
        assert user_tag is None or isinstance(user_tag, Tag), \
            _raise_exception(TypeError(f"user_tag must be {None} or {Tag.__name__}"))

        super().__init__()

        self.user_tag: Optional[Tag] = user_tag
        self.title: str = ""
        self.join_date: datetime = datetime.fromtimestamp(0)
        self.user_icon_url: str = ""

        self.parse()

    def __iter__(self):
        yield "name", self.name
        yield "status", self.status
        yield "title", self.title
        yield "join_date", self.join_date
        yield "user_icon_url", self.user_icon_url

    def parse(self, user_tag: Tag = None):
        """
        Parse a user page, overrides any information already present in the object.

        :param user_tag: The tag from which to parse the user information.
        """
        assert user_tag is None or isinstance(user_tag, Tag), \
            _raise_exception(TypeError(f"user_tag must be {None} or {Tag.__name__}"))

        self.user_tag = user_tag or self.user_tag
        if self.user_tag is None:
            return

        parsed: dict = parse_user_tag(self.user_tag)

        self.name = parsed["name"]
        self.status = parsed["status"]
        self.title = parsed["title"]
        self.join_date = parsed["join_date"]


class User(UserBase):
    """
    Contains complete user information gathered from userpages.
    """

    def __init__(self, user_page: BeautifulSoup = None):
        """
        :param user_page: The page from which to parse the user information.
        """
        assert user_page is None or isinstance(user_page, BeautifulSoup), \
            _raise_exception(TypeError(f"user_page must be {None} or {BeautifulSoup.__name__}"))

        super().__init__()

        self.user_page: Optional[BeautifulSoup] = user_page
        self.title: str = ""
        self.join_date: datetime = datetime.fromtimestamp(0)
        self.profile: str = ""
        self.stats: UserStats = UserStats(0, 0, 0, 0, 0, 0, 0, 0)
        self.info: dict[str, str] = {}
        self.contacts: dict[str, str] = {}
        self.user_icon_url: str = ""
        self.watched: bool = False
        self.watched_toggle_link: Optional[str] = None
        self.blocked: bool = False
        self.blocked_toggle_link: Optional[str] = None

        self.parse()

    def __iter__(self):
        yield "name", self.name
        yield "status", self.status
        yield "title", self.title
        yield "join_date", self.join_date
        yield "profile", self.profile
        yield "stats", self.stats._asdict()
        yield "info", self.info
        yield "contacts", self.contacts
        yield "user_icon_url", self.user_icon_url
        yield "watched", self.watched
        yield "watched_toggle_link", self.watched_toggle_link
        yield "blocked", self.blocked
        yield "blocked_toggle_link", self.blocked_toggle_link

    def parse(self, user_page: BeautifulSoup = None):
        """
        Parse a user page, overrides any information already present in the object.

        :param user_page: The page from which to parse the user information.
        """
        assert user_page is None or isinstance(user_page, BeautifulSoup), \
            _raise_exception(TypeError(f"user_page must be {None} or {BeautifulSoup.__name__}"))

        self.user_page = user_page or self.user_page
        if self.user_page is None:
            return

        check_page_raise(self.user_page)

        parsed: dict = parse_user_page(self.user_page)

        self.name = parsed["name"]
        self.status = parsed["status"]
        self.profile = parsed["profile"]
        self.title = parsed["title"]
        self.join_date = parsed["join_date"]
        self.stats = UserStats(*parsed["stats"])
        self.info = parsed["info"]
        self.contacts = parsed["contacts"]
        self.user_icon_url = parsed["user_icon_url"]
        self.watched = parsed["watch"] is None and parsed["unwatch"] is not None
        self.watched_toggle_link = parsed["watch"] or parsed["unwatch"] or None
        self.blocked = parsed["block"] is None and parsed["unblock"] is not None
        self.blocked_toggle_link = parsed["block"] or parsed["unblock"] or None
