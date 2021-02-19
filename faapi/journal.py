from typing import Dict
from typing import Optional
from typing import Union

from bs4 import BeautifulSoup
from bs4.element import Tag

from .parse import check_page_raise
from .parse import parse_journal_page
from .parse import parse_journal_section


class Journal:
    def __init__(self, journal_item: Union[Tag, BeautifulSoup] = None):
        assert journal_item is None or isinstance(journal_item, BeautifulSoup) or isinstance(journal_item, Tag)

        self.journal_item: Optional[Union[Tag, BeautifulSoup]] = journal_item

        self.id: int = 0
        self.title: str = ""
        self.date: str = ""
        self.author: str = ""
        self.content: str = ""

        self.parse()

    def __iter__(self):
        yield "id", self.id
        yield "title", self.title
        yield "date", self.date
        yield "author", self.author
        yield "content", self.content

    def __repr__(self):
        return repr(dict(self))

    def __str__(self):
        return f"{self.id} {self.author} {self.title}"

    def parse(self, journal_item: Union[Tag, BeautifulSoup] = None):
        assert journal_item is None or isinstance(journal_item, BeautifulSoup) or isinstance(journal_item, Tag)
        self.journal_item = journal_item if journal_item is not None else self.journal_item
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
        self.author = parsed.get("author", "")
        self.date = parsed["date"]
        self.content = parsed["content"]
