from re import search as re_search

from bs4 import BeautifulSoup
from bs4 import ResultSet
from bs4.element import Tag


def page_parse(text: str) -> BeautifulSoup:
    return BeautifulSoup(text, "lxml")


def sub_parse_figure(figure: Tag) -> dict:
    sub_id: int = int(re_search(r"sid-(\d+)", figure["id"]).group(1))
    sub_caption_links: ResultSet = figure.find("figcaption").findAll("a")
    sub_title: str = sub_caption_links[0].text
    sub_author: str = sub_caption_links[1].text
    sub_rating: str = re_search(r"r-(\w+)", figure["class"]).group(1)

    return {
        "id": sub_id,
        "title": sub_title,
        "author": sub_author,
        "rating": sub_rating
    }
