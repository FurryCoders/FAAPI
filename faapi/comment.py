from datetime import datetime
from functools import reduce
from typing import Optional
from typing import Union

from bs4.element import Tag

import faapi
from .exceptions import _raise_exception
from .parse import html_to_bbcode
from .parse import parse_comment_tag


class Comment:
    """
    Contains comment information and references to replies and parent objects.
    """

    def __init__(self, tag: Optional[Tag] = None,
                 parent: Optional[Union[faapi.submission.Submission, faapi.journal.Journal]] = None):
        """
        :param tag: The comment tag from which to parse information
        :param parent: The parent object of the comment
        """
        assert tag is None or isinstance(tag, Tag), _raise_exception(TypeError(f"tag must be {None} or {Tag.__name__}"))

        self.comment_tag: Optional[Tag] = tag

        self.id: int = 0
        self.author: faapi.user.UserPartial = faapi.user.UserPartial()
        self.date: datetime = datetime.fromtimestamp(0)
        self.text: str = ""
        self.replies: list[Comment] = []
        self.reply_to: Optional[Union[Comment, int]] = None
        self.edited: bool = False
        self.hidden: bool = False
        self.parent: Optional[Union[faapi.submission.Submission, faapi.journal.Journal]] = parent

        self.parse()

    def __hash__(self) -> int:
        return hash((self.id, type(self.parent), self.parent))

    def __eq__(self, other) -> bool:
        if isinstance(other, Comment):
            return other.id == self.id and self.parent == other.parent
        elif isinstance(other, int):
            return other == self.id
        return False

    def __gt__(self, other) -> bool:
        if isinstance(other, Comment):
            return self.id > other.id
        elif isinstance(other, int):
            return self.id > other
        return False

    def __ge__(self, other) -> bool:
        if isinstance(other, Comment):
            return self.id >= other.id
        elif isinstance(other, int):
            return self.id >= other
        return False

    def __lt__(self, other) -> bool:
        if isinstance(other, Comment):
            return self.id < other.id
        elif isinstance(other, int):
            return self.id < other
        return False

    def __le__(self, other) -> bool:
        if isinstance(other, Comment):
            return self.id <= other.id
        elif isinstance(other, int):
            return self.id <= other
        return False

    def __iter__(self):
        yield "id", self.id
        yield "author", dict(self.author)
        yield "date", self.date
        yield "text", self.text
        yield "replies", _sort_comments_dict(self.replies)
        yield "reply_to", dict(_remove_recursion(self.reply_to)) if isinstance(self.reply_to, Comment) \
            else self.reply_to
        yield "edited", self.edited
        yield "hidden", self.hidden
        yield "parent", None if self.parent is None else dict(self.parent)

    def __repr__(self):
        return self.__str__()

    def __str__(self):
        return f"{self.id} {self.author}".rstrip()

    @property
    def text_bbcode(self) -> str:
        """
        The comment text formatted to BBCode

        :return: BBCode text
        """
        return html_to_bbcode(self.text)

    @property
    def url(self):
        """
        Compose the full URL to the comment.

        :return: The URL to the comment.
        """
        return "" if self.parent is None else f"{self.parent.url}#cid:{self.id}"

    def parse(self, comment_tag: Optional[Tag] = None):
        """
        Parse a comment tag, overrides any information already present in the object.

        :param comment_tag: The comment tag from which to parse information
        """
        assert comment_tag is None or isinstance(comment_tag, Tag), \
            _raise_exception(TypeError(f"tag must be {None} or {Tag.__name__}"))

        self.comment_tag = comment_tag or self.comment_tag
        if self.comment_tag is None:
            return

        parsed: dict = parse_comment_tag(self.comment_tag)

        self.id = parsed["id"]
        self.date = datetime.fromtimestamp(parsed["timestamp"])
        self.author = faapi.user.UserPartial()
        self.author.name = parsed["user_name"]
        self.author.title = parsed["user_title"]
        self.author.avatar_url = parsed["avatar_url"]
        self.text = parsed["text"]
        self.replies = []
        self.reply_to = parsed["parent"]
        self.edited = parsed["edited"]
        self.hidden = parsed["hidden"]


def sort_comments(comments: list[Comment]) -> list[Comment]:
    """
    Sort a list of comments into a tree structure. Replies are overwritten.

    :param comments: A list of Comment objects (flat or tree-structured)
    :return: A tree-structured list of comments with replies
    """
    for comment in (comments := flatten_comments(comments)):
        comment.replies = [_set_reply_to(c, comment) for c in comments if c.reply_to == comment]
    return [c for c in comments if c.reply_to is None]


def flatten_comments(comments: list[Comment]) -> list[Comment]:
    """
    Flattens a list of comments. Replies are not modified.

    :param comments: A list of Comment objects (flat or tree-structured)
    :return: A flat date-sorted (ascending) list of comments
    """
    replies: list[Comment] = comments
    comments_flat: list[Comment] = []

    while replies:
        comments_flat.extend(replies)
        replies = [r for c in replies for r in c.replies]

    return sorted(set(comments_flat))


def _set_reply_to(comment: Comment, reply_to: Union[Comment, int]) -> Comment:
    comment.reply_to = reply_to
    return comment


def _sort_comments_dict(comments: list[Comment]) -> list[dict]:
    comments_flat = flatten_comments(comments)
    comments_levels: list[list[Comment]] = [[c for c in comments_flat if not c.reply_to]]

    comments_flat = [c for c in comments_flat if c not in comments_levels[-1]]

    while comments_flat:
        comments_levels.append([c for c in comments_flat if c.reply_to in comments_levels[-1]])
        comments_flat = [c for c in comments_flat if c not in comments_levels[-1]]

    comments_levels.reverse()

    comments_dicts: list[dict] = reduce(
        lambda prev, curr: [
            dict(_remove_recursion(c)) | {"replies": [cd for cd in prev if cd["reply_to"] == c]}
            for c in curr
        ],
        comments_levels,
        []
    )
    return comments_dicts


def _remove_recursion(comment: Comment) -> Comment:
    comment_new: Comment = Comment()

    comment_new.comment_tag = comment.comment_tag
    comment_new.id = comment.id
    comment_new.author = comment.author
    comment_new.date = comment.date
    comment_new.text = comment.text
    comment_new.replies = []
    comment_new.reply_to = comment.reply_to.id if isinstance(comment.reply_to, Comment) else comment.reply_to
    comment_new.edited = comment.edited
    comment_new.hidden = comment.hidden
    comment_new.parent = None

    return comment_new
