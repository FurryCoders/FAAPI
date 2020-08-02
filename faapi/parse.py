from bs4 import BeautifulSoup


def page_parse(text: str) -> BeautifulSoup:
    return BeautifulSoup(text, "lxml")
