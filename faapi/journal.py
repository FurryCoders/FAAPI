from typing import Optional

from bs4 import BeautifulSoup
from bs4.element import Tag

from faapi.parse import parse_journal_page
from faapi.parse import parse_journal_section


class Journal:
    def __init__(self, journal_section: Optional[Tag] = None, journal_page: Optional[BeautifulSoup] = None):
        assert journal_section is None or isinstance(journal_section, Tag)
        assert journal_page is None or isinstance(journal_page, BeautifulSoup)

        self.journal_section: Optional[Tag] = journal_section
        self.journal_page: Optional[BeautifulSoup] = journal_page

        self.id: int = 0
        self.title: str = ""
        self.date: str = ""
        self.author: str = ""
        self.content: str = ""

        self.parse_journal_section()
        self.parse_journal_page()

    def __iter__(self):
        yield "id", self.id
        yield "title", self.title
        yield "date", self.date
        yield "author", self.author
        yield "content", self.content

    def __repr__(self):
        return repr(dict(self))

    def parse_journal_section(self):
        if self.journal_section is None:
            return

        parsed: dict = parse_journal_section(self.journal_section)

        self.id = parsed["id"]
        self.title = parsed["title"]
        self.date = parsed["date"]
        self.content = parsed["content"]

    def parse_journal_page(self):
        if self.journal_page is None:
            return

        parsed: dict = parse_journal_page(self.journal_page)

        self.id = parsed["id"]
        self.title = parsed["title"]
        self.author = parsed["author"]
        self.date = parsed["date"]
        self.content = parsed["content"]
