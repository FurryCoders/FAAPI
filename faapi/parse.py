from typing import Dict
from typing import List
from typing import Union

from bs4 import BeautifulSoup
from bs4 import ResultSet
from bs4.element import Tag
from dateutil.parser import parse as parse_date


def parse_page(text: str) -> BeautifulSoup:
    return BeautifulSoup(text, "lxml")


def parse_journal_section(section_tag: Tag) -> Dict[str, Union[int, str]]:
    id_: int = int(section_tag.attrs["id"][4:])
    title: str = section_tag.find("h2").text.strip()
    date: str = parse_date(section_tag.find("span", class_="popup_date")["title"].strip()).strftime("%Y-%m-%d")
    content: str = section_tag.find("div", class_="journal-body").text.strip()

    return {
        "id": id_,
        "title": title,
        "date": date,
        "content": content,
    }


def parse_journal_page(journal_page: BeautifulSoup) -> Dict[str, Union[int, str]]:
    tag_id: Tag = journal_page.find("meta", property="og:url")
    tag_title: Tag = journal_page.find("h2", class_="journal-title")
    tag_author: Tag = journal_page.find("a", class_="current")
    tag_date: Tag = journal_page.find("span", class_="popup_date")
    tag_body: Tag = journal_page.find("div", class_="journal-content")

    id_: int = int(tag_id["content"].strip("/").split("/")[-1])
    title: str = tag_title.text.strip()
    author: str = tag_author["href"].strip("/").split("/")[-1]
    date: str = parse_date(tag_date["title"].strip()).strftime("%Y-%m-%d")
    content: str = "".join(map(str, tag_body.children)).strip()

    return {
        "id": id_,
        "author": author,
        "title": title,
        "date": date,
        "content": content,
    }


def parse_submission_figure(figure_tag: Tag) -> Dict[str, Union[int, str]]:
    caption_links: ResultSet = figure_tag.find("figcaption").findAll("a")

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
    if sub_page.find("section", class_="notice-message"):
        raise Exception("Error: notice-message section found")

    tag_id: Tag = sub_page.find("meta", property="og:url")
    tag_sub_info: Tag = sub_page.find("div", class_="submission-id-sub-container")
    tag_title: Tag = tag_sub_info.find("div", class_="submission-title")
    tag_author: Tag = tag_sub_info.find("a")
    tag_date: Tag = sub_page.find("span", class_="popup_date")
    tag_tags: ResultSet = sub_page.find("section", class_="tags-row").findAll("a")
    tag_rating: Tag = sub_page.find("div", class_="rating").find("span")
    tag_info: ResultSet = sub_page.find("section", class_="info text").findAll("div")
    tag_category1: Tag = tag_info[1].find("span", class_="category-name")
    tag_category2: Tag = tag_info[1].find("span", class_="type-name")
    tag_species: Tag = tag_info[2].find("span")
    tag_gender: Tag = tag_info[3].find("span")
    tag_description: Tag = sub_page.find("div", class_="submission-description")
    tag_file_url: Tag = sub_page.find("div", class_="download").find("a")

    id_: int = int(tag_id["content"].strip("/").split("/")[-1])
    title: str = tag_title.text.strip()
    author: str = tag_author.text.strip()
    date: str = parse_date(tag_date["title"].strip()).strftime("%Y-%m-%d")
    tags: [str] = [t.text.strip() for t in tag_tags]
    category: str = tag_category1.text.strip() + "/" + tag_category2.text.strip()
    species: str = tag_species.text.strip()
    gender: str = tag_gender.text.strip()
    rating: str = tag_rating.text.strip()
    description: str = "".join(map(str, tag_description.children)).strip()
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
        "file_url": file_url,
    }
