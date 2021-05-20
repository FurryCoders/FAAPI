from datetime import datetime
from re import Pattern
from re import compile as re_compile
from re import match
from re import search
from re import sub
from typing import Dict
from typing import List
from typing import Optional
from typing import Tuple
from typing import Union

from bs4 import BeautifulSoup
from bs4.element import NavigableString
from bs4.element import Tag
from dateutil.parser import parse as parse_date

from .exceptions import DisabledAccount
from .exceptions import NoTitle
from .exceptions import NonePage
from .exceptions import NoticeMessage
from .exceptions import ServerError

mentions_regexp: Pattern = re_compile(r"^(?:(?:https?://)?(?:www.)?furaffinity.net)?/user/([^/#]+).*$")


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
    elif notice := page.select_one("section.notice-message"):
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


def username_url(username: str) -> str:
    return sub(r"[^a-z0-9.~-]", "", username.lower())


def parse_mentions(tag: Tag) -> List[str]:
    return sorted(set(ms := list(filter(bool, (
        username_url(m.group(1).lower())
        for a in tag.select("a")
        if (m := match(mentions_regexp, a.attrs.get("href"))) is not None
    )))), key=ms.index)


def parse_journal_section(section_tag: Tag) -> Dict[str, Union[int, str, datetime]]:
    id_: int = int(section_tag.attrs["id"][4:])
    title: str = section_tag.select_one("h2").text.strip()
    date: datetime = parse_date(section_tag.select_one("span.popup_date")["title"].strip())
    content: str = "".join(map(str, (tag_content := section_tag.select_one("div.journal-body")).children))
    mentions: List[str] = parse_mentions(tag_content)

    return {
        "id": id_,
        "title": title,
        "date": date,
        "content": content,
        "mentions": mentions,
    }


def parse_journal_page(journal_page: BeautifulSoup) -> Dict[str, Union[int, str, datetime]]:
    user_info: Dict[str, str] = parse_user_folder(journal_page)
    tag_id: Tag = journal_page.select_one("meta[property='og:url']")
    tag_title: Tag = journal_page.select_one("h2.journal-title")
    tag_date: Tag = journal_page.select_one("span.popup_date")
    tag_content: Tag = journal_page.select_one("div.journal-content")

    id_: int = int(tag_id["content"].strip("/").split("/")[-1])
    title: str = tag_title.text.strip()
    date: datetime = parse_date(tag_date["title"].strip())
    content: str = "".join(map(str, tag_content.children)).strip()
    mentions: List[str] = parse_mentions(tag_content)

    return {
        **user_info,
        "id": id_,
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
    thumbnail_url: str = "https:" + figure_tag.select_one("img").attrs["src"]

    return {
        "id": id_,
        "title": title,
        "author": author,
        "rating": rating,
        "type": type_,
        "thumbnail_url": thumbnail_url,
    }


def parse_submission_author(author_tag: Tag) -> Dict[str, str]:
    tag_author: Tag = author_tag.select_one("div.submission-id-sub-container")
    tag_author_name: Tag = tag_author.select_one("a > strong")
    tag_author_icon: Tag = author_tag.select_one("img.submission-user-icon")

    author_name: str = tag_author_name.text.strip()
    author_title: str = [*filter(bool, [child.strip()
                                        for child in tag_author.children
                                        if isinstance(child, NavigableString)][3:])][-1]
    author_title = author_title if tag_author.select_one('a[href$="/#tip"]') is None else sub(r"\|$", "", author_title)
    author_title = author_title.strip("\xA0 ")  # NBSP
    author_icon_url: str = "https:" + tag_author_icon["src"]

    return {
        "author": author_name,
        "author_title": author_title,
        "author_icon_url": author_icon_url,
    }


def parse_submission_page(sub_page: BeautifulSoup) -> Dict[str, Union[int, str, List[str], datetime]]:
    tag_id: Tag = sub_page.select_one("meta[property='og:url']")
    tag_sub_info: Tag = sub_page.select_one("div.submission-id-sub-container")
    tag_title: Tag = tag_sub_info.select_one("div.submission-title")
    tag_author: Tag = sub_page.select_one("div.submission-id-container")
    tag_date: Tag = sub_page.select_one("span.popup_date")
    tag_tags: List[Tag] = sub_page.select("section.tags-row a")
    tag_rating: Tag = sub_page.select_one("div.rating span")
    tag_type: Tag = sub_page.select_one("div#submission_page[class^='page-content-type']")
    tag_info: Tag = sub_page.select_one("section.info.text")
    tag_category1: Tag = tag_info.select_one("span.category-name")
    tag_category2: Tag = tag_info.select_one("span.type-name")
    tag_species: Tag = (info_spans := tag_info.select("span"))[2]
    tag_gender: Tag = info_spans[3]
    tag_description: Tag = sub_page.select_one("div.submission-description")
    tag_folder: Tag = sub_page.select_one("a.button[href^='/scraps/'],a.button[href^='/gallery/']")
    tag_file_url: Tag = sub_page.select_one("div.download a")
    tag_thumbnail_url: Tag = sub_page.select_one("img#submissionImg")

    id_: int = int(tag_id["content"].strip("/").split("/")[-1])
    title: str = tag_title.text.strip()
    date: datetime = parse_date(
        tag_date["title"].strip()
        if match(r"^[A-Za-z]+ \d+,.*$", tag_date["title"])
        else tag_date.text.strip()
    )
    tags: [str] = [t.text.strip() for t in tag_tags]
    category: str = tag_category1.text.strip() + "/" + tag_category2.text.strip()
    species: str = tag_species.text.strip()
    gender: str = tag_gender.text.strip()
    rating: str = tag_rating.text.strip()
    type_: str = tag_type["class"][0][18:]
    description: str = "".join(map(str, tag_description.children)).strip()
    mentions: List[str] = parse_mentions(tag_description)
    folder: str = match(r"^/(scraps|gallery)/.*$", tag_folder["href"]).group(1).lower()
    file_url: str = "https:" + tag_file_url["href"]
    thumbnail_url: str = ("https:" + tag_thumbnail_url["data-preview-src"]) if tag_thumbnail_url else ""

    return {
        "id": id_,
        "title": title,
        **parse_submission_author(tag_author),
        "date": date,
        "tags": tags,
        "category": category,
        "species": species,
        "gender": gender,
        "rating": rating,
        "type": type_,
        "description": description,
        "mentions": mentions,
        "folder": folder,
        "file_url": file_url,
        "thumbnail_url": thumbnail_url,
    }


def parse_user_page(user_page: BeautifulSoup) -> Dict[str, str]:
    tag_name: Tag = user_page.select_one("div.username")
    tag_profile: Tag = user_page.select_one("div.userpage-profile")
    tag_title_join_date: Tag = user_page.select_one("div.userpage-flex-item.username > span")
    tag_stats: Tag = user_page.select_one("div.userpage-section-right div.table")
    tag_info: Tag = user_page.select_one("div#userpage-contact-item")
    tag_contacts: Tag = user_page.select_one("div#userpage-contact")
    tag_user_icon_url: Tag = user_page.select_one("img.user-nav-avatar")

    status: str = (u := tag_name.find("span").text.strip())[0]
    name: str = u[1:]
    title: str = (ttd := tag_title_join_date.text.rsplit("|", 1))[0].strip()
    join_date: datetime = parse_date(ttd[1].strip().split(":", 1)[1])
    profile: str = "".join(map(str, tag_profile.children)).strip()
    stats: tuple[int, ...] = tuple(map(lambda s: int(s.split(":")[1]),
                                       filter(bool, map(str.strip, tag_stats.text.split("\n")))))
    info: Dict[str, str] = {
        tb.select_one("div").text.strip(): [*filter(bool, [c.strip()
                                                           for c in tb.children
                                                           if isinstance(c, NavigableString)])][-1]
        for tb in tag_info.select("div.table-row")
        if "profile-empty" not in tb.attrs.get("class", [])
    } if tag_info is not None else {}
    contacts: Dict[str, str] = {
        pc.select_one("span").text.strip(): a["href"] if (a := pc.select_one("a")) else
        [*filter(bool, map(str.strip, pc.text.split("\n")))][-1]
        for pc in tag_contacts.select("div.user-contact-user-info")
    } if tag_contacts is not None else {}
    user_icon_url: str = "https:" + tag_user_icon_url["src"]

    return {
        "name": name,
        "status": status,
        "title": title,
        "join_date": join_date,
        "profile": profile,
        "stats": stats,
        "info": info,
        "contacts": contacts,
        "user_icon_url": user_icon_url,
    }


def parse_user_tag(user_tag: Tag) -> Dict[str, str]:
    status: str = (u := [*filter(bool, map(str.strip, user_tag.text.split("\n")))])[0][0]
    name: str = u[0][1:]
    title: str = (ttd := u[1].rsplit("|", 1))[0].strip()
    join_date: datetime = parse_date(ttd[1].strip().split(":", 1)[1])

    return {
        "user_name": name,
        "user_status": status,
        "user_title": title,
        "user_join_date": join_date,
    }


def parse_user_folder(folder_page: BeautifulSoup) -> Dict[str, str]:
    return {
        **parse_user_tag(folder_page.select_one("div.userpage-flex-item.username")),
        "user_icon_url": "https:" + folder_page.select_one("img.user-nav-avatar")["src"],
    }


def parse_user_submissions(submissions_page: BeautifulSoup) -> Dict[str, Union[str, List[Tag], bool]]:
    user_info: Dict[str, str] = parse_user_folder(submissions_page)
    figures: List[Tag] = submissions_page.select("figure[id^='sid-']")

    return {
        **user_info,
        "figures": figures,
        "last_page": not figures,
    }


def parse_user_favorites(favorites_page: BeautifulSoup) -> Dict[str, Union[str, List[Tag], bool]]:
    parsed_submissions = parse_user_submissions(favorites_page)
    tag_next_page: Optional[Tag] = favorites_page.select_one("a[class~=button][class~=standard][class~=right]")
    next_page: str = tag_next_page["href"].split("/", 3)[-1] if tag_next_page else ""

    return {
        **parsed_submissions,
        "next_page": next_page,
    }


def parse_user_journals(journals_page: BeautifulSoup) -> Dict[str, Union[str, List[Tag], bool]]:
    user_info: Dict[str, str] = parse_user_folder(journals_page)
    sections: List[Tag] = journals_page.select("section[id^='jid:']")

    return {
        **user_info,
        "sections": sections,
        "last_page": not sections,
    }


def parse_search_submissions(search_page: BeautifulSoup) -> Dict[str, Union[List[Tag], bool]]:
    tag_stats: Tag = search_page.select_one("div[id='query-stats']")
    for div in tag_stats.select("div"):
        div.decompose()
    a, b, tot = map(int, search(r"(\d+)[^\d]*(\d+)[^\d]*(\d+)", tag_stats.text.strip()).groups())
    figures: List[Tag] = search_page.select("figure[id^='sid-']")

    return {
        "from": (a or 1) - 1,
        "to": (b or 1) - 1,
        "total": tot,
        "figures": figures,
        "last_page": b >= tot
    }


def parse_watchlist(watch_page: BeautifulSoup) -> List[Tuple[str, str]]:
    tags_users: List[Tag] = watch_page.select("div.watch-list-items")
    return [((u := t.text.strip().replace(" ", ""))[0], u[1:]) for t in tags_users]
