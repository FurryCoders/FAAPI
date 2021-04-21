from typing import Dict
from typing import List
from typing import Optional
from typing import Union

from bs4 import BeautifulSoup
from bs4.element import Tag

from .connection import join_url
from .connection import root
from .parse import check_page_raise
from .parse import parse_journal_page
from .parse import parse_journal_section
from .user import User


class Journal:
    def __init__(self, journal_item: Union[Tag, BeautifulSoup] = None):
        assert journal_item is None or isinstance(journal_item, (BeautifulSoup, Tag))

        self.journal_item: Optional[Union[Tag, BeautifulSoup]] = journal_item

        self.id: int = 0
        self.title: str = ""
        self.date: str = ""
        self.author: User = User()
        self.content: str = ""
        self.mentions: List[str] = []

        self.parse()

    def __iter__(self):
        yield "id", self.id
        yield "title", self.title
        yield "date", self.date
        yield "author", dict(self.author)
        yield "content", self.content
        yield "mentions", self.mentions

    def __repr__(self):
        return repr(dict(self))

    def __str__(self):
        return f"{self.id} {self.author} {self.title}"

    @property
    def url(self):
        return join_url(root, "journal", self.id)

    def parse(self, journal_item: Union[Tag, BeautifulSoup] = None):
        assert journal_item is None or isinstance(journal_item, (BeautifulSoup, Tag))
        self.journal_item = journal_item or self.journal_item
        if self.journal_item is None:
            return

        parsed: Dict[str, Union[int, str]]
        if isinstance(self.journal_item, BeautifulSoup):
            check_page_raise(self.journal_item)
            parsed = parse_journal_page(self.journal_item)
        else:
            parsed = parse_journal_section(self.journal_item)

        self.id = parsed["id"]
        self.title = parsed["title"]
        self.author.name = parsed.get("user_name", "")
        self.author.status = parsed.get("user_status", "")
        self.author.user_icon_url = parsed.get("user_icon_url", "")
        self.date = parsed["date"]
        self.content = parsed["content"]
        self.mentions = parsed["mentions"]
