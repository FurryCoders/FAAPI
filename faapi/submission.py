from collections import namedtuple
from datetime import datetime
from typing import Optional

from .connection import join_url
from .connection import root
from .exceptions import _raise_exception
from .parse import BeautifulSoup
from .parse import Tag
from .parse import check_page_raise
from .parse import html_to_bbcode
from .parse import parse_comments
from .parse import parse_submission_figure
from .parse import parse_submission_page
from .user import UserPartial


class SubmissionStats(namedtuple("SubmissionStats", ["views", "comments", "favorites"])):
    """
    This object contains the submission's statistics:
    * views
    * comments
    * favorites
    """


class SubmissionUserFolder(namedtuple("SubmissionUserFolder", ["name", "url", "group"])):
    """
    This object contains a submission's folder details:
    * name: str the name of the folder
    * url: str the URL to the folder
    * group: str the group the folder belongs to
    """


class SubmissionBase:
    """
    Base class for the submission objects.
    """

    def __init__(self):
        self.id: int = 0
        self.title: str = ""
        self.author: UserPartial = UserPartial()

    def __hash__(self) -> int:
        return hash(self.id)

    def __eq__(self, other) -> bool:
        if isinstance(other, SubmissionBase):
            return other.id == self.id
        elif isinstance(other, int):
            return other == self.id
        return False

    def __gt__(self, other) -> bool:
        if isinstance(other, SubmissionBase):
            return self.id > other.id
        elif isinstance(other, int):
            return self.id > other
        return False

    def __ge__(self, other) -> bool:
        if isinstance(other, SubmissionBase):
            return self.id >= other.id
        elif isinstance(other, int):
            return self.id >= other
        return False

    def __lt__(self, other) -> bool:
        if isinstance(other, SubmissionBase):
            return self.id < other.id
        elif isinstance(other, int):
            return self.id < other
        return False

    def __le__(self, other) -> bool:
        if isinstance(other, SubmissionBase):
            return self.id <= other.id
        elif isinstance(other, int):
            return self.id <= other
        return False

    def __iter__(self):
        yield "id", self.id
        yield "title", self.title
        yield "author", dict(self.author)

    def __repr__(self):
        return self.__str__()

    def __str__(self):
        return f"{self.id} {self.author} {self.title}"

    @property
    def url(self):
        """
        Compose the full URL to the submission.

        :return: The URL to the submission.
        """
        return join_url(root, "view", self.id)


class SubmissionPartial(SubmissionBase):
    """
    Contains partial submission information gathered from submissions pages (gallery, scraps, etc.).
    """

    def __init__(self, submission_figure: Optional[Tag] = None):
        """
        :param submission_figure: The figure tag from which to parse the submission information.
        """
        assert submission_figure is None or isinstance(submission_figure, Tag), \
            _raise_exception(TypeError(f"submission_figure must be {None} or {BeautifulSoup.__name__}"))

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

    def parse(self, submission_figure: Optional[Tag] = None):
        """
        Parse a submission figure Tag, overrides any information already present in the object.

        :param submission_figure: The optional figure tag from which to parse the submission.
        """
        assert submission_figure is None or isinstance(submission_figure, Tag), \
            _raise_exception(TypeError(f"submission_figure must be {None} or {BeautifulSoup.__name__}"))

        self.submission_figure = submission_figure or self.submission_figure
        if self.submission_figure is None:
            return

        parsed: dict = parse_submission_figure(self.submission_figure)

        self.id = parsed["id"]
        self.title = parsed["title"]
        self.author.name = parsed["author"]
        self.rating = parsed["rating"]
        self.type = parsed["type"]
        self.thumbnail_url = parsed["thumbnail_url"]


class Submission(SubmissionBase):
    """
    Contains complete submission information gathered from submission pages, including comments.
    """

    def __init__(self, submission_page: Optional[BeautifulSoup] = None):
        """
        :param submission_page: The page from which to parse the submission information.
        """
        assert submission_page is None or isinstance(submission_page, BeautifulSoup), \
            _raise_exception(TypeError(f"submission_page must be {None} or {BeautifulSoup.__name__}"))

        super().__init__()

        self.submission_page: Optional[BeautifulSoup] = submission_page
        self.date: datetime = datetime.fromtimestamp(0)
        self.tags: list[str] = []
        self.category: str = ""
        self.species: str = ""
        self.gender: str = ""
        self.rating: str = ""
        self.stats: SubmissionStats = SubmissionStats(0, 0, 0)
        self.type: str = ""
        self.description: str = ""
        self.footer: str = ""
        self.mentions: list[str] = []
        self.folder: str = ""
        self.user_folders: list[SubmissionUserFolder] = []
        self.file_url: str = ""
        self.thumbnail_url: str = ""
        self.prev: Optional[int] = None
        self.next: Optional[int] = None
        self.favorite: bool = False
        self.favorite_toggle_link: str = ""
        from .comment import Comment
        self.comments: list[Comment] = []

        self.parse()

    def __iter__(self):
        yield "id", self.id
        yield "title", self.title
        yield "author", dict(self.author)
        yield "date", self.date
        yield "tags", self.tags
        yield "category", self.category
        yield "species", self.species
        yield "gender", self.gender
        yield "rating", self.rating
        yield "stats", self.stats._asdict()
        yield "type", self.type
        yield "description", self.description
        yield "footer", self.footer
        yield "mentions", self.mentions
        yield "folder", self.folder
        yield "user_folders", [f._asdict() for f in self.user_folders]
        yield "file_url", self.file_url
        yield "thumbnail_url", self.thumbnail_url
        yield "prev", self.prev
        yield "next", self.next
        yield "favorite", self.favorite
        yield "favorite_toggle_link", self.favorite_toggle_link
        from .comment import _remove_recursion
        yield "comments", [dict(_remove_recursion(c)) for c in self.comments]

    @property
    def description_bbcode(self) -> str:
        """
        The submission description formatted to BBCode

        :return: BBCode description
        """
        return html_to_bbcode(self.description)

    @property
    def footer_bbcode(self) -> str:
        """
        The submission footer formatted to BBCode

        :return: BBCode footer
        """
        return html_to_bbcode(self.footer)

    def parse(self, submission_page: Optional[BeautifulSoup] = None):
        """
        Parse a submission page, overrides any information already present in the object.

        :param submission_page: The optional page from which to parse the submission.
        """
        assert submission_page is None or isinstance(submission_page, BeautifulSoup), \
            _raise_exception(TypeError(f"submission_page must be {None} or {BeautifulSoup.__name__}"))

        self.submission_page = submission_page or self.submission_page
        if self.submission_page is None:
            return

        check_page_raise(self.submission_page)

        parsed: dict = parse_submission_page(self.submission_page)

        self.id = parsed["id"]
        self.title = parsed["title"]
        self.author.name = parsed["author"]
        self.author.title = parsed["author_title"]
        self.author.avatar_url = parsed["author_icon_url"]
        self.date = parsed["date"]
        self.tags = parsed["tags"]
        self.category = parsed["category"]
        self.species = parsed["species"]
        self.gender = parsed["gender"]
        self.rating = parsed["rating"]
        self.stats = SubmissionStats(parsed["views"], parsed["comment_count"], parsed["favorites"])
        self.type = parsed["type"]
        self.description = parsed["description"]
        self.footer = parsed["footer"]
        self.mentions = parsed["mentions"]
        self.folder = parsed["folder"]
        self.user_folders = [SubmissionUserFolder(*f) for f in parsed["user_folders"]]
        self.file_url = parsed["file_url"]
        self.thumbnail_url = parsed["thumbnail_url"]
        self.prev = parsed["prev"]
        self.next = parsed["next"]
        self.favorite = parsed["unfav_link"] is not None
        self.favorite_toggle_link = parsed["fav_link"] or parsed["unfav_link"]
        from .comment import sort_comments, Comment
        self.comments = sort_comments([Comment(t, self) for t in parse_comments(self.submission_page)])
