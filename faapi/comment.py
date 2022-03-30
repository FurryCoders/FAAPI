from datetime import datetime
from typing import Optional
from typing import Union

from bs4.element import Tag

from faapi import Journal
from faapi import Submission
from faapi import UserPartial
from .parse import parse_comment_tag


class Comment:
    def __init__(self, tag: Tag = None, parent: Union[Submission, Journal] = None):
        assert tag is None or isinstance(tag, Tag)

        self.tag: Optional[Tag] = tag

        self.id: int = 0
        self.author: UserPartial = UserPartial()
        self.date: datetime = datetime.fromtimestamp(0)
        self.text: Optional[Tag] = None
        self.parent: Optional[Union[Submission, Journal]] = parent
        self.replies: list['Comment'] = []
        self.reply_to: Optional[int] = None
        self.edited: bool = False
        self.hidden: bool = False

        self.parse()

    def __iter__(self):
        yield "id", self.id
        yield "author", dict(self.author)
        yield "date", self.date
        yield "text", self.text
        yield "parent", None if self.parent is None else dict(self.parent)
        yield "replies", [dict(r) for r in self.replies]
        yield "reply_to", self.reply_to
        yield "edited", self.edited
        yield "hidden", self.hidden

    def __repr__(self):
        return self.__str__()

    def __str__(self):
        return f"{self.id} {self.author}".rstrip()

    @property
    def url(self):
        return "" if self.parent is None else f"{self.parent.url}#cid:{self.id}"

    def parse(self, tag: Tag = None):
        if tag is not None:
            self.tag = tag
        elif self.tag is None:
            return

        parsed: dict = parse_comment_tag(self.tag)

        self.id = parsed["id"]
        self.date = datetime.fromtimestamp(parsed["timestamp"])
        self.author = UserPartial()
        self.author.name = parsed["user_name"]
        self.author.title = parsed["user_title"]
        self.author.user_icon_url = parsed["user_icon_url"]
        self.text = parsed["text"]
        self.replies = []
        self.reply_to = parsed["parent"]
        self.edited = parsed["edited"]
        self.hidden = parsed["hidden"]


def sort_comments(comments: list[Comment]) -> list[Comment]:
    comments = sorted(flatten_comments(comments), key=lambda c: c.date)
    for comment in comments:
        comment.replies = [c for c in comments if c.reply_to == comment.id]
    return [c for c in comments if c.reply_to is None]


def flatten_comments(comments: list[Comment]) -> list[Comment]:
    return [c for comment in comments for c in [comment, *flatten_comments(comment.replies)]]
