from datetime import datetime
from typing import List
from typing import Optional

from .connection import join_url
from .connection import root
from .parse import BeautifulSoup
from .parse import Tag
from .parse import check_page_raise
from .parse import parse_submission_figure
from .parse import parse_submission_page
from .user import UserPartial


class SubmissionBase:
    def __init__(self):
        self.id: int = 0
        self.title: str = ""
        self.author: UserPartial = UserPartial()

    def __iter__(self):
        yield "id", self.id
        yield "title", self.title
        yield "author", dict(self.author)

    def __repr__(self):
        return repr(dict(self))

    def __str__(self):
        return f"{self.id} {self.author} {self.title}"

    @property
    def url(self):
        return join_url(root, "view", self.id)


class SubmissionPartial(SubmissionBase):
    def __init__(self, submission_figure: Tag = None):
        assert submission_figure is None or isinstance(submission_figure, Tag)

        super().__init__()

        self.submission_figure: Optional[Tag] = submission_figure
        self.rating: str = ""
        self.type: str = ""
        self.thumbnail_url: str = ""

        self.parse()

    def __iter__(self):
        yield "id", self.id
        yield "title", self.title
        yield "author", dict(self.author)
        yield "rating", self.rating
        yield "type", self.type
        yield "thumbnail_url", self.thumbnail_url

    def parse(self, submission_figure: Tag = None):
        assert submission_figure is None or isinstance(submission_figure, Tag)
        self.submission_figure = submission_figure or self.submission_figure
        if self.submission_figure is None:
            return

        parsed: dict = parse_submission_figure(self.submission_figure)

        self.id: int = parsed["id"]
        self.title: str = parsed["title"]
        self.author.name = parsed["author"]
        self.rating: str = parsed["rating"]
        self.type: str = parsed["type"]
        self.thumbnail_url: str = parsed["thumbnail_url"]


class Submission(SubmissionBase):
    def __init__(self, submission_page: BeautifulSoup = None):
        assert submission_page is None or isinstance(submission_page, BeautifulSoup)

        super().__init__()

        self.submission_page: Optional[BeautifulSoup] = submission_page
        self.date: datetime = datetime.fromtimestamp(0)
        self.tags: List[str] = []
        self.category: str = ""
        self.species: str = ""
        self.gender: str = ""
        self.rating: str = ""
        self.type: str = ""
        self.description: str = ""
        self.mentions: List[str] = []
        self.folder: str = ""
        self.file_url: str = ""
        self.thumbnail_url: str = ""

        self.parse()

    def __iter__(self):
        yield "id", self.id
        yield "title", self.title
        yield "author", dict(self.author)
        yield "date", self.date.timetuple()
        yield "tags", self.tags
        yield "category", self.category
        yield "species", self.species
        yield "gender", self.gender
        yield "rating", self.rating
        yield "type", self.type
        yield "description", self.description
        yield "mentions", self.mentions
        yield "folder", self.folder
        yield "file_url", self.file_url
        yield "thumbnail_url", self.thumbnail_url

    def parse(self, submission_page: BeautifulSoup = None):
        assert submission_page is None or isinstance(submission_page, BeautifulSoup)
        self.submission_page = submission_page or self.submission_page
        if self.submission_page is None:
            return

        check_page_raise(self.submission_page)

        parsed: dict = parse_submission_page(self.submission_page)

        self.id: int = parsed["id"]
        self.title: str = parsed["title"]
        self.author.name = parsed["author"]
        self.author.title = parsed["author_title"]
        self.author.user_icon_url = parsed["author_icon_url"]
        self.date: datetime = parsed["date"]
        self.tags: List[str] = parsed["tags"]
        self.category: str = parsed["category"]
        self.species: str = parsed["species"]
        self.gender: str = parsed["gender"]
        self.rating: str = parsed["rating"]
        self.type: str = parsed["type"]
        self.description: str = parsed["description"]
        self.mentions: List[str] = parsed["mentions"]
        self.folder: str = parsed["folder"]
        self.file_url: str = parsed["file_url"]
        self.thumbnail_url: str = parsed["thumbnail_url"]
