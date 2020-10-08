from typing import List
from typing import Optional

from .parse import BeautifulSoup
from .parse import Tag
from .parse import parse_submission_figure
from .parse import parse_submission_page


class SubmissionPartial:
    def __init__(self, sub_figure: Optional[Tag] = None):
        assert sub_figure is None or isinstance(sub_figure, Tag)

        self.sub_figure = sub_figure

        self.id: int = 0
        self.title: str = ""
        self.author: str = ""
        self.rating: str = ""
        self.type: str = ""

        self.parse_figure_tag()

    def __iter__(self):
        yield "id", self.id
        yield "title", self.title
        yield "author", self.author
        yield "rating", self.rating
        yield "type", self.type

    def __repr__(self):
        return repr(dict(self))

    def parse_figure_tag(self):
        if self.sub_figure is None:
            return

        parsed: dict = parse_submission_figure(self.sub_figure)

        self.id: int = parsed["id"]
        self.title: str = parsed["title"]
        self.author: str = parsed["author"]
        self.rating: str = parsed["rating"]
        self.type: str = parsed["type"]


class Submission:
    def __init__(self, sub_page: Optional[BeautifulSoup] = None):
        assert sub_page is None or isinstance(sub_page, BeautifulSoup)

        self.sub_page = sub_page

        self.id: int = 0
        self.title: str = ""
        self.author: str = ""
        self.date: str = ""
        self.tags: List[str] = []
        self.category: str = ""
        self.species: str = ""
        self.gender: str = ""
        self.rating: str = ""
        self.description: str = ""
        self.file_url: str = ""

        self.parse_page()

    def __iter__(self):
        yield "id", self.id
        yield "title", self.title
        yield "author", self.author
        yield "date", self.date
        yield "tags", self.tags
        yield "category", self.category
        yield "species", self.species
        yield "gender", self.gender
        yield "rating", self.rating
        yield "description", self.description
        yield "file_url", self.file_url

    def __repr__(self):
        return repr(dict(self))

    def parse_page(self):
        if self.sub_page is None:
            return
        elif self.sub_page.find("section", attrs={"class": "notice-message"}):
            raise Exception("Error: notice-message section found")

        parsed: dict = parse_submission_page(self.sub_page)

        self.id: int = parsed["id"]
        self.title: str = parsed["title"]
        self.author: str = parsed["author"]
        self.date: str = parsed["date"]
        self.tags: List[str] = parsed["tags"]
        self.category: str = parsed["category"]
        self.species: str = parsed["species"]
        self.gender: str = parsed["gender"]
        self.rating: str = parsed["rating"]
        self.description: str = parsed["description"]
        self.file_url: str = parsed["file_url"]
