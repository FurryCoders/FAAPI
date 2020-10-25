from typing import Dict
from typing import Optional
from typing import Union

from bs4 import BeautifulSoup
from bs4.element import Tag

from faapi.parse import parse_journal_page
from faapi.parse import parse_journal_section


class Journal:
    def __init__(self, journal_item: Optional[Union[Tag, BeautifulSoup]] = None):
        assert journal_item is None or isinstance(journal_item, BeautifulSoup) or isinstance(journal_item, Tag)

        self.journal_item: Optional[Union[Tag, BeautifulSoup]] = journal_item

        self.id: int = 0
        self.title: str = ""
        self.date: str = ""
        self.author: str = ""
        self.content: str = ""

        self.parse_journal()

    def __iter__(self):
        yield "id", self.id
        yield "title", self.title
        yield "date", self.date
        yield "author", self.author
        yield "content", self.content

    def __repr__(self):
        return repr(dict(self))

    def parse_journal(self):
        if self.journal_item is None:
            return

        parsed: Dict[str, Union[int, str]]
        if isinstance(self.journal_item, BeautifulSoup):
            parsed = parse_journal_page(self.journal_item)
        else:
            parsed = parse_journal_section(self.journal_item)

        self.id = parsed["id"]
        self.title = parsed["title"]
        self.title = parsed.get("author", "")
        self.date = parsed["date"]
        self.content = parsed["content"]
