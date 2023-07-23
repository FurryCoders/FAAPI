from collections import namedtuple
from datetime import datetime
from typing import Optional
from typing import Union

from .connection import join_url
from .connection import root
from .exceptions import _raise_exception
from .parse import BeautifulSoup
from .parse import check_page_raise
from .parse import html_to_bbcode
from .parse import parse_comments
from .parse import parse_journal_page
from .parse import parse_journal_section
from .parse import Tag
from .user import UserPartial


class JournalStats(namedtuple("JournalStats", ["comments"])):
    """
    This object contains the journal's statistics:
    * comments
    """


class JournalBase:
    def __init__(self):
        self.id: int = 0
        self.title: str = ""
        self.date: datetime = datetime.fromtimestamp(0)
        self.author: UserPartial = UserPartial()
        self.stats: JournalStats = JournalStats(0)
        self.content: str = ""
        self.mentions: list[str] = []

    def __hash__(self) -> int:
        return hash(self.id)

    def __eq__(self, other) -> bool:
        if isinstance(other, JournalBase):
            return other.id == self.id
        elif isinstance(other, int):
            return other == self.id
        return False

    def __gt__(self, other) -> bool:
        if isinstance(other, JournalBase):
            return self.id > other.id
        elif isinstance(other, int):
            return self.id > other
        return False

    def __ge__(self, other) -> bool:
        if isinstance(other, JournalBase):
            return self.id >= other.id
        elif isinstance(other, int):
            return self.id >= other
        return False

    def __lt__(self, other) -> bool:
        if isinstance(other, JournalBase):
            return self.id < other.id
        elif isinstance(other, int):
            return self.id < other
        return False

    def __le__(self, other) -> bool:
        if isinstance(other, JournalBase):
            return self.id <= other.id
        elif isinstance(other, int):
            return self.id <= other
        return False

    def __iter__(self):
        yield "id", self.id
        yield "title", self.title
        yield "date", self.date
        yield "author", dict(self.author)
        yield "stats", self.stats._asdict()
        yield "content", self.content
        yield "mentions", self.mentions

    def __repr__(self):
        return self.__str__()

    def __str__(self):
        return f"{self.id} {self.author} {self.title}"

    @property
    def content_bbcode(self) -> str:
        """
        The journal content formatted to BBCode

        :return: BBCode content
        """
        return html_to_bbcode(self.content)

    @property
    def url(self) -> str:
        """
        Compose the full URL to the journal.

        :return: The URL to the journal.
        """
        return join_url(root, "journal", self.id)


class JournalPartial(JournalBase):
    """
    Contains partial journal information gathered from journals pages.
    """

    def __init__(self, journal_tag: Optional[Tag] = None):
        """
        :param journal_tag: The tag from which to parse the journal.
        """
        assert journal_tag is None or isinstance(journal_tag, Tag), \
            _raise_exception(TypeError(f"journal_item must be {None} or {Tag.__name__}"))
        self.journal_tag: Optional[Tag] = journal_tag

        super(JournalPartial, self).__init__()

        self.parse()

    def parse(self, journal_tag: Optional[Union[Tag, BeautifulSoup]] = None):
        """
        Parse a journal tag, overrides any information already present in the object.

        :param journal_tag: The tag from which to parse the journal.
        """
        assert journal_tag is None or isinstance(journal_tag, BeautifulSoup), \
            _raise_exception(TypeError(f"journal_item must be {None} or {BeautifulSoup.__name__}"))

        self.journal_tag = journal_tag or self.journal_tag
        if self.journal_tag is None:
            return

        parsed: dict = parse_journal_section(self.journal_tag)

        # noinspection DuplicatedCode
        self.id = parsed["id"]
        self.title = parsed["title"]
        self.author.name = parsed.get("user_name", "")
        self.author.status = parsed.get("user_status", "")
        self.author.title = parsed.get("user_title", "")
        self.author.join_date = parsed.get("user_join_date", "")
        self.author.avatar_url = parsed.get("avatar_url", "")
        self.stats = JournalStats(parsed["comments"])
        self.date = parsed["date"]
        self.content = parsed["content"]
        self.mentions = parsed["mentions"]


class Journal(JournalBase):
    """
    Contains complete journal information gathered from journal pages, including comments.
    """

    def __init__(self, journal_page: Optional[BeautifulSoup] = None):
        """
        :param journal_page: The page from which to parse the journal.
        """
        assert journal_page is None or isinstance(journal_page, BeautifulSoup), \
            _raise_exception(TypeError(f"journal_item must be {None} or {BeautifulSoup.__name__}"))
        self.journal_page: Optional[BeautifulSoup] = journal_page

        super(Journal, self).__init__()

        self.header: str = ""
        self.footer: str = ""
        from .comment import Comment
        self.comments: list[Comment] = []

        self.parse()

    def __iter__(self):
        for k, v in super(Journal, self).__iter__():
            yield k, v
        yield "header", self.header
        yield "footer", self.footer
        from .comment import _sort_comments_dict
        yield "comments", _sort_comments_dict(self.comments)

    @property
    def header_bbcode(self) -> str:
        """
        The journal header formatted to BBCode

        :return: BBCode header
        """
        return html_to_bbcode(self.header)

    @property
    def footer_bbcode(self) -> str:
        """
        The journal footer formatted to BBCode

        :return: BBCode footer
        """
        return html_to_bbcode(self.footer)

    def parse(self, journal_page: Optional[Union[Tag, BeautifulSoup]] = None):
        """
        Parse a journal page, overrides any information already present in the object.

        :param journal_page: The page from which to parse the journal.
        """
        assert journal_page is None or isinstance(journal_page, BeautifulSoup), \
            _raise_exception(TypeError(f"journal_item must be {None} or {BeautifulSoup.__name__}"))

        self.journal_page = journal_page or self.journal_page
        if self.journal_page is None:
            return

        check_page_raise(self.journal_page)

        parsed: dict = parse_journal_page(self.journal_page)

        # noinspection DuplicatedCode
        self.id = parsed["id"]
        self.title = parsed["title"]
        self.author.name = parsed["user_info"]["name"]
        self.author.status = parsed["user_info"]["status"]
        self.author.title = parsed["user_info"]["title"]
        self.author.join_date = parsed["user_info"]["join_date"]
        self.author.avatar_url = parsed["user_info"]["avatar_url"]
        self.stats = JournalStats(parsed["comments"])
        self.date = parsed["date"]
        self.content = parsed["content"]
        self.header = parsed["header"]
        self.footer = parsed["footer"]
        self.mentions = parsed["mentions"]
        from .comment import sort_comments, Comment
        self.comments = sort_comments([Comment(t, self) for t in parse_comments(self.journal_page)])
