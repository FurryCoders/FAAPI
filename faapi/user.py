from typing import Optional

from .parse import BeautifulSoup
from .parse import check_page_raise
from .parse import parse_user_page


class User:
    def __init__(self, user_page: BeautifulSoup = None):
        assert user_page is None or isinstance(user_page, BeautifulSoup)

        self.user_page: Optional[BeautifulSoup] = user_page

        self.name: str = ""
        self.status: str = ""
        self.profile: str = ""
        self.user_icon_url: str = ""

        self.parse()

    def __iter__(self):
        yield "name", self.name
        yield "status", self.status
        yield "profile", self.profile
        yield "user_icon_url", self.user_icon_url

    def __repr__(self):
        return repr(dict(self))

    def __str__(self):
        return self.status + self.name

    def parse(self, user_page: BeautifulSoup = None):
        assert user_page is None or isinstance(user_page, BeautifulSoup)
        self.user_page = user_page if user_page is not None else self.user_page
        if self.user_page is None:
            return

        check_page_raise(self.user_page)

        parsed: dict = parse_user_page(self.user_page)

        self.name: str = parsed["name"]
        self.status: str = parsed["status"]
        self.profile: str = parsed["profile"]
        self.user_icon_url: str = parsed["user_icon_url"]
