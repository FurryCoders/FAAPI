from re import Pattern
from re import compile as re_compile
from re import match
from re import sub
from typing import Dict
from typing import List
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
    elif notice := page.find("section", class_="notice-message"):
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
        for a in tag.findAll("a")
        if (m := match(mentions_regexp, a.attrs.get("href"))) is not None
    )))


def parse_journal_section(section_tag: Tag) -> Dict[str, Union[int, str]]:
    id_: int = int(section_tag.attrs["id"][4:])
    title: str = section_tag.find("h2").text.strip()
    date: str = parse_date(section_tag.find("span", class_="popup_date")["title"].strip()).strftime("%Y-%m-%d")
    content: str = "".join(map(str, (tag_content := section_tag.find("div", class_="journal-body")).children))
    mentions: List[str] = parse_mentions(tag_content)

    return {
        "id": id_,
        "title": title,
        "date": date,
        "content": content,
        "mentions": mentions,
    }


def parse_journal_page(journal_page: BeautifulSoup) -> Dict[str, Union[int, str]]:
    check_page(journal_page)

    tag_id: Tag = journal_page.find("meta", property="og:url")
    tag_title: Tag = journal_page.find("h2", class_="journal-title")
    tag_author: Tag = journal_page.find("a", class_="current")
    tag_date: Tag = journal_page.find("span", class_="popup_date")
    tag_content: Tag = journal_page.find("div", class_="journal-content")

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
    caption_links: List[Tag] = figure_tag.find("figcaption").findAll("a")

    id_: int = int(caption_links[0]["href"].strip("/").split("/")[-1])
    title: str = caption_links[0].text
    author: str = caption_links[1].text
    rating: str = figure_tag["class"][0][2:]
    type_: str = figure_tag["class"][1][2:]

    return {
        "id": id_,
        "title": title,
        "author": author,
        "rating": rating,
        "type": type_,
    }


def parse_submission_page(sub_page: BeautifulSoup) -> Dict[str, Union[int, str, List[str]]]:
    check_page(sub_page)

    tag_id: Tag = sub_page.find("meta", property="og:url")
    tag_sub_info: Tag = sub_page.find("div", class_="submission-id-sub-container")
    tag_title: Tag = tag_sub_info.find("div", class_="submission-title")
    tag_author: Tag = tag_sub_info.find("a")
    tag_date: Tag = sub_page.find("span", class_="popup_date")
    tag_tags: List[Tag] = sub_page.find("section", class_="tags-row").findAll("a")
    tag_rating: Tag = sub_page.find("div", class_="rating").find("span")
    tag_info: List[Tag] = sub_page.find("section", class_="info text").findAll("div")
    tag_category1: Tag = tag_info[1].find("span", class_="category-name")
    tag_category2: Tag = tag_info[1].find("span", class_="type-name")
    tag_species: Tag = tag_info[2].find("span")
    tag_gender: Tag = tag_info[3].find("span")
    tag_description: Tag = sub_page.find("div", class_="submission-description")
    tag_folder: Tag = next(filter(
        lambda a: a["href"].startswith("/scraps/") or a["href"].startswith("/gallery/"),
        sub_page.findAll("a", class_="button")
    ))
    tag_file_url: Tag = sub_page.find("div", class_="download").find("a")

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
