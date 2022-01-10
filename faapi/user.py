from collections import namedtuple
from datetime import datetime
from typing import Optional

from .connection import join_url
from .connection import root
from .parse import BeautifulSoup
from .parse import Tag
from .parse import check_page_raise
from .parse import parse_user_page
from .parse import parse_user_tag
from .parse import username_url


class UserStats(namedtuple("UserStats", ["views", "submissions", "favs", "comments_earned",
                                         "comments_made", "journals", "watched_by", "watching"])):
    """
    This object contains a user's statistics:
    * views
    * submissions
    * favs
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
        return username_url(self.name.lower())

    @property
    def url(self):
        """
        Compose the full URL to the user.

        :return: The URL to the user.
        """
        return join_url(root, "user", self.name_url)


class UserPartial(UserBase):
    """
    This class contains a user's partial information.
    """

    def __init__(self, user_tag: Tag = None):
        """
        :param user_tag: The tag from which to parse the user information.
        """
        assert user_tag is None or isinstance(user_tag, Tag)

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
        assert user_tag is None or isinstance(user_tag, Tag)
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
    This class contains a user's full information.
    """

    def __init__(self, user_page: BeautifulSoup = None):
        """
        :param user_page: The page from which to parse the user information.
        """
        assert user_page is None or isinstance(user_page, BeautifulSoup)

        super().__init__()

        self.user_page: Optional[BeautifulSoup] = user_page
        self.title: str = ""
        self.join_date: datetime = datetime.fromtimestamp(0)
        self.profile: str = ""
        self.stats: UserStats = UserStats(0, 0, 0, 0, 0, 0, 0, 0)
        self.info: dict[str, str] = {}
        self.contacts: dict[str, str] = {}
        self.user_icon_url: str = ""

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

    def parse(self, user_page: BeautifulSoup = None):
        """
        Parse a user page, overrides any information already present in the object.

        :param user_page: The page from which to parse the user information.
        """
        assert user_page is None or isinstance(user_page, BeautifulSoup)
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
