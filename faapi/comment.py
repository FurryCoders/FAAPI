from datetime import datetime
from typing import Optional
from typing import Union

from bs4.element import Tag

import faapi
from .parse import parse_comment_tag


class Comment:
    """
    Contains comment information.
    """

    def __init__(self, tag: Tag = None, parent: Union[faapi.submission.Submission, faapi.journal.Journal] = None):
        """
        :param tag: The comment tag from which to parse information
        :param parent: The parent object of the comment
        """
        assert tag is None or isinstance(tag, Tag)

        self.tag: Optional[Tag] = tag

        self.id: int = 0
        self.author: faapi.user.UserPartial = faapi.user.UserPartial()
        self.date: datetime = datetime.fromtimestamp(0)
        self.text: str = ""
        self.replies: list['Comment'] = []
        self.reply_to: Optional[int] = None
        self.edited: bool = False
        self.hidden: bool = False
        self.parent: Optional[Union[faapi.submission.Submission, faapi.journal.Journal]] = parent

        self.parse()

    def __iter__(self):
        yield "id", self.id
        yield "author", dict(self.author)
        yield "date", self.date
        yield "text", self.text
        yield "replies", [dict(r) for r in self.replies]
        yield "reply_to", self.reply_to
        yield "edited", self.edited
        yield "hidden", self.hidden
        yield "parent", None if self.parent is None else dict(self.parent)

    def __repr__(self):
        return self.__str__()

    def __str__(self):
        return f"{self.id} {self.author}".rstrip()

    @property
    def url(self):
        return "" if self.parent is None else f"{self.parent.url}#cid:{self.id}"

    def parse(self, tag: Tag = None):
        """
        Parse a comment tag, overrides any information already present in the object.

        :param tag: The comment tag from which to parse information
        """
        assert tag is None or isinstance(tag, Tag)

        if tag is not None:
            self.tag = tag
        elif self.tag is None:
            return

        parsed: dict = parse_comment_tag(self.tag)

        self.id = parsed["id"]
        self.date = datetime.fromtimestamp(parsed["timestamp"])
        self.author = faapi.user.UserPartial()
        self.author.name = parsed["user_name"]
        self.author.title = parsed["user_title"]
        self.author.user_icon_url = parsed["user_icon_url"]
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
    comments = sorted(flatten_comments(comments), key=lambda c: c.date)
    for comment in comments:
        comment.replies = [c for c in comments if c.reply_to == comment.id]
    return [c for c in comments if c.reply_to is None]


def flatten_comments(comments: list[Comment]) -> list[Comment]:
    """
    Flattens a list of comments. Replies are not added if missing.

    :param comments: A list of Comment objects (flat or tree-structured)
    :return: A flat date-sorted (ascending) list of comments
    """
    return [c for comment in comments for c in [comment, *flatten_comments(comment.replies)]]


def _remove_parents(comment: Comment) -> Comment:
    comment_new: Comment = Comment()

    comment_new.tag = comment.tag
    comment_new.id = comment.id
    comment_new.author = comment.author
    comment_new.date = comment.date
    comment_new.text = comment.text
    comment_new.replies = [_remove_parents(c) for c in comment.replies]
    comment_new.reply_to = comment.reply_to
    comment_new.edited = comment.edited
    comment_new.hidden = comment.hidden
    comment_new.parent = None

    return comment_new
