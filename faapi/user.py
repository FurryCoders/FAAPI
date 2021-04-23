from collections import namedtuple
from datetime import datetime
from typing import Dict
from typing import Optional
from typing import Type

from bs4.element import Tag

from .connection import join_url
from .connection import root
from .parse import BeautifulSoup
from .parse import check_page_raise
from .parse import parse_user_page
from .parse import parse_user_tag
from .parse import username_url

UserStats: Type['UserStats'] = namedtuple(
    "UserStats",
    ["views", "submissions", "favs", "comments_earned", "comments_made", "journals"]
)


class UserBase:
    def __init__(self):
        self.name: str = ""
        self.status: str = ""

    def __iter__(self):
        yield "name", self.name
        yield "status", self.status

    def __repr__(self):
        return repr(dict(self))

    def __str__(self):
        return self.status + self.name

    @property
    def name_url(self):
        return username_url(self.name.lower())

    @property
    def url(self):
        return join_url(root, "user", self.name_url)


class UserPartial(UserBase):
    def __init__(self, user_tag: Tag = None):
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
        yield "join_date", self.join_date.timetuple()
        yield "user_icon_url", self.user_icon_url

    def parse(self, user_tag: Tag = None):
        assert user_tag is None or isinstance(user_tag, Tag)
        self.user_tag = user_tag or self.user_tag
        if self.user_tag is None:
            return

        parsed: dict = parse_user_tag(self.user_tag)

        self.name: str = parsed["name"]
        self.status: str = parsed["status"]
        self.title: str = parsed["title"]
        self.join_date: datetime = parsed["join_date"]


class User(UserBase):
    def __init__(self, user_page: BeautifulSoup = None):
        assert user_page is None or isinstance(user_page, BeautifulSoup)

        super().__init__()

        self.user_page: Optional[BeautifulSoup] = user_page
        self.title: str = ""
        self.join_date: datetime = datetime.fromtimestamp(0)
        self.profile: str = ""
        self.stats: UserStats = UserStats(0, 0, 0, 0, 0, 0)
        self.info: Dict[str, str] = {}
        self.contacts: Dict[str, str] = {}
        self.user_icon_url: str = ""

        self.parse()

    def __iter__(self):
        yield "name", self.name
        yield "status", self.status
        yield "title", self.title
        yield "join_date", self.join_date.timetuple()
        yield "profile", self.profile
        yield "stats", self.stats._asdict()
        yield "info", self.info
        yield "contacts", self.contacts
        yield "user_icon_url", self.user_icon_url

    def parse(self, user_page: BeautifulSoup = None):
        assert user_page is None or isinstance(user_page, BeautifulSoup)
        self.user_page = user_page or self.user_page
        if self.user_page is None:
            return

        check_page_raise(self.user_page)

        parsed: dict = parse_user_page(self.user_page)

        self.name: str = parsed["name"]
        self.status: str = parsed["status"]
        self.profile: str = parsed["profile"]
        self.title: str = parsed["title"]
        self.join_date: datetime = parsed["join_date"]
        self.stats: UserStats = UserStats(*parsed["stats"])
        self.info: Dict[str, str] = parsed["info"]
        self.contacts: Dict[str, str] = parsed["contacts"]
        self.user_icon_url: str = parsed["user_icon_url"]
