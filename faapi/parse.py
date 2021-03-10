from re import Pattern
from re import compile as re_compile
from re import match
from re import sub
from typing import Dict
from typing import List
from typing import Tuple
from typing import Union

from bs4 import BeautifulSoup
from bs4.element import Tag
from dateutil.parser import parse as parse_date

from .exceptions import DisabledAccount
from .exceptions import NoTitle
from .exceptions import NonePage
from .exceptions import NoticeMessage
from .exceptions import ServerError

mentions_regexp: Pattern = re_compile(r"^(?:(?:https?://)?(?:www.)?furaffinity.net)?/user/(.+)$")


def parse_page(text: str) -> BeautifulSoup:
    return BeautifulSoup(text, "lxml")


def check_page(page: BeautifulSoup) -> int:
    """
    0 if page is okay
    1 if page is None
    2 if page has no title
    3 if page is from a disabled account
    4 if page is a system error
    5 if page has a notice-message (error)
    """

    if page is None:
        return 1
    elif not (title := page.title.text.lower()):
        return 2
    elif title.startswith("account disabled"):
        return 3
    elif title == "system error":
        return 4
    elif notice := page.select_one("section[class~=notice-message]"):
        return 3 if (p := notice.find("p")) and "deactivated" in p.text.lower() else 5

    return 0


def check_page_raise(page: BeautifulSoup):
    if (check := check_page(page)) == 1:
        raise NonePage
    elif check == 2:
        raise NoTitle
    elif check == 3:
        raise DisabledAccount
    elif check == 4:
        raise ServerError
    elif check == 5:
        raise NoticeMessage


def parse_mentions(tag: Tag) -> List[str]:
    return sorted(filter(bool, set(
        sub(r"[^a-z0-9.~-]", "", m.group(1).lower())
        for a in tag.select("a")
        if (m := match(mentions_regexp, a.attrs.get("href"))) is not None
    )))


def parse_journal_section(section_tag: Tag) -> Dict[str, Union[int, str]]:
    id_: int = int(section_tag.attrs["id"][4:])
    title: str = section_tag.select_one("h2").text.strip()
    date: str = parse_date(section_tag.select_one("span[class~=popup_date]")["title"].strip()).strftime("%Y-%m-%d")
    content: str = "".join(map(str, (tag_content := section_tag.select_one("div[class~=journal-body]")).children))
    mentions: List[str] = parse_mentions(tag_content)

    return {
        "id": id_,
        "title": title,
        "date": date,
        "content": content,
        "mentions": mentions,
    }


def parse_journal_page(journal_page: BeautifulSoup) -> Dict[str, Union[int, str]]:
    tag_id: Tag = journal_page.select_one("meta[property='og:url']")
    tag_title: Tag = journal_page.select_one("h2[class~=journal-title]")
    tag_author: Tag = journal_page.select_one("a[class~=current]")
    tag_date: Tag = journal_page.select_one("span[class~=popup_date]")
    tag_content: Tag = journal_page.select_one("div[class~=journal-content]")

    id_: int = int(tag_id["content"].strip("/").split("/")[-1])
    title: str = tag_title.text.strip()
    author: str = tag_author["href"].strip("/").split("/")[-1]
    date: str = parse_date(tag_date["title"].strip()).strftime("%Y-%m-%d")
    content: str = "".join(map(str, tag_content.children)).strip()
    mentions: List[str] = parse_mentions(tag_content)

    return {
        "id": id_,
        "author": author,
        "title": title,
        "date": date,
        "content": content,
        "mentions": mentions,
    }


def parse_submission_figure(figure_tag: Tag) -> Dict[str, Union[int, str]]:
    id_: int = int(figure_tag.attrs["id"][4:])
    title: str = figure_tag.select_one("figcaption a[href^='/view/']").attrs["title"]
    author: str = figure_tag.select_one("figcaption a[href^='/user/']").attrs["title"]
    rating: str = next(c for c in figure_tag["class"] if c.startswith("r-"))[2:]
    type_: str = next(c for c in figure_tag["class"] if c.startswith("t-"))[2:]

    return {
        "id": id_,
        "title": title,
        "author": author,
        "rating": rating,
        "type": type_,
    }


def parse_submission_page(sub_page: BeautifulSoup) -> Dict[str, Union[int, str, List[str]]]:
    tag_id: Tag = sub_page.select_one("meta[property='og:url']")
    tag_sub_info: Tag = sub_page.select_one("div[class~=submission-id-sub-container]")
    tag_title: Tag = tag_sub_info.select_one("div[class~=submission-title]")
    tag_author: Tag = tag_sub_info.select_one("a")
    tag_date: Tag = sub_page.select_one("span[class~=popup_date]")
    tag_tags: List[Tag] = sub_page.select("section[class~=tags-row] a")
    tag_rating: Tag = sub_page.select_one("div[class~=rating] span")
    tag_info: Tag = sub_page.select_one("section[class~=info][class~=text]")
    tag_category1: Tag = tag_info.select_one("span[class~=category-name]")
    tag_category2: Tag = tag_info.select_one("span[class~=type-name]")
    tag_species: Tag = tag_info.select("span")[2]
    tag_gender: Tag = tag_info.select("span")[3]
    tag_description: Tag = sub_page.select_one("div[class~=submission-description]")
    tag_folder: Tag = sub_page.select_one("a[class~=button][href^='/scraps/'],a[class~=button][href^='/gallery/']")
    tag_file_url: Tag = sub_page.select_one("div[class~=download] a")

    id_: int = int(tag_id["content"].strip("/").split("/")[-1])
    title: str = tag_title.text.strip()
    author: str = tag_author.text.strip()
    date: str = parse_date(
        tag_date["title"].strip()
        if match(r"^[A-Za-z]+ \d+,.*$", tag_date["title"])
        else tag_date.text.strip()
    ).strftime("%Y-%m-%d")
    tags: [str] = [t.text.strip() for t in tag_tags]
    category: str = tag_category1.text.strip() + "/" + tag_category2.text.strip()
    species: str = tag_species.text.strip()
    gender: str = tag_gender.text.strip()
    rating: str = tag_rating.text.strip()
    description: str = "".join(map(str, tag_description.children)).strip()
    mentions: List[str] = parse_mentions(tag_description)
    folder: str = match(r"^/(scraps|gallery)/.*$", tag_folder["href"]).group(1).lower()
    file_url: str = "https:" + tag_file_url["href"]

    return {
        "id": id_,
        "title": title,
        "author": author,
        "date": date,
        "tags": tags,
        "category": category,
        "species": species,
        "gender": gender,
        "rating": rating,
        "description": description,
        "mentions": mentions,
        "folder": folder,
        "file_url": file_url,
    }


def parse_user_page(user_page: BeautifulSoup) -> Dict[str, str]:
    tag_name: Tag = user_page.select_one("div[class~=username]")
    tag_profile: Tag = user_page.select_one("div[class~=userpage-profile]")

    status: str = (u := tag_name.find("span").text.strip())[0]
    name: str = u[1:]
    profile: str = "".join(map(str, tag_profile.children)).strip()

    return {
        "name": name,
        "status": status,
        "profile": profile,
    }


def parse_watchlist(watch_page: BeautifulSoup) -> List[Tuple[str, str]]:
    tags_users: List[Tag] = watch_page.select("div[class~=watch-list-items]")
    return [((u := t.text.strip().replace(" ", ""))[0], u[1:]) for t in tags_users]
