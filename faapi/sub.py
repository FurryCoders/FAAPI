from re import search as re_search
from typing import List

from bs4 import BeautifulSoup
from bs4 import ResultSet
from bs4.element import Tag
from dateutil.parser import parse


class SubPartial:
    def __init__(self):
        self.id: int = 0
        self.title: str = ""
        self.author: str = ""
        self.rating: str = ""
        self.type: str = ""

    @classmethod
    def parse_figure_tag(cls, figure_tag: Tag) -> 'SubPartial':
        sub = SubPartial()

        caption_links: ResultSet = figure_tag.find("figcaption").findAll("a")

        sub.id = int(caption_links[0].strip("/").strip("/")[-1])
        sub.title = caption_links[0].text
        sub.author = caption_links[1].text
        sub.rating, sub.type = re_search(r"r-(\w+)[^t]*t-(\w+)", figure_tag["class"]).groups()

        return sub


class Sub:
    def __init__(self, sub_page: BeautifulSoup = None):
        assert isinstance(sub_page, BeautifulSoup)

        self.sub_page = sub_page

        self.id: int = 0
        self.title: str = ""
        self.author: str = ""
        self.date: str = ""
        self.tags: List[str] = []
        self.category: str = ""
        self.species: str = ""
        self.gender: str = ""
        self.rating: str = ""
        self.description: str = ""
        self.file_url: str = ""

        self.parse_page()

    def __iter__(self):
        yield "id", self.id
        yield "title", self.title
        yield "author", self.author
        yield "date", self.date
        yield "tags", self.tags
        yield "category", self.category
        yield "species", self.species
        yield "gender", self.gender
        yield "rating", self.rating
        yield "description", self.description
        yield "file_url", self.file_url

    def parse_page(self):
        if self.sub_page is None:
            return

        tag_id: Tag = self.sub_page.find("meta", property="og:url")
        tag_sub_info: Tag = self.sub_page.find("div", attrs={"class": "submission-id-sub-container"})
        tag_title: Tag = tag_sub_info.find("div", attrs={"class": "submission-title"})
        tag_author: Tag = tag_sub_info.find("a")
        tag_date: Tag = self.sub_page.find("span", attrs={"class": "popup_date"})
        tag_tags: ResultSet = self.sub_page.find("section", attrs={"class": "tags-row"}).findAll("a")
        tag_rating: Tag = self.sub_page.find("div", attrs={"class": "rating"}).find("span")
        tag_info: ResultSet = self.sub_page.find("section", attrs={"class": "info text"}).findAll("div")
        tag_category1: Tag = tag_info[1].find("span", attrs={"class": "category-name"})
        tag_category2: Tag = tag_info[1].find("span", attrs={"class": "type-name"})
        tag_species: Tag = tag_info[2].find("span")
        tag_gender: Tag = tag_info[3].find("span")
        tag_description: Tag = self.sub_page.find("div", attrs={"class": "submission-description"})
        tag_file_url: Tag = self.sub_page.find("div", attrs={"class": "download"}).find("a")

        self.id = int(tag_id["content"].strip("/").split("/")[-1])
        self.title = tag_title.text.strip()
        self.author = tag_author.text.strip()
        self.date = parse(tag_date.text.strip()).strftime("%Y-%m-%d")
        self.tags = [t.text.strip() for t in tag_tags]
        self.category = tag_category1.text.strip() + "/" + tag_category2.text.strip()
        self.species = tag_species.text.strip()
        self.gender = tag_gender.text.strip()
        self.rating = tag_rating.text.strip()
        self.description = "".join(map(str, tag_description.children)).strip()
        self.file_url = "https:" + tag_file_url["href"]
