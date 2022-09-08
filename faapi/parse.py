from datetime import datetime
from re import MULTILINE
from re import Match
from re import Pattern
from re import compile as re_compile
from re import match
from re import search
from re import sub
from typing import Any
from typing import Optional
from typing import Union

from bbcode import Parser as BBCodeParser  # type:ignore
from bs4 import BeautifulSoup
from bs4.element import NavigableString
from bs4.element import Tag
from dateutil.parser import parse as parse_date
from htmlmin import minify  # type:ignore

from .connection import root
from .exceptions import DisabledAccount
from .exceptions import NoTitle
from .exceptions import NonePage
from .exceptions import NotFound
from .exceptions import NoticeMessage
from .exceptions import ParsingError
from .exceptions import ServerError
from .exceptions import _raise_exception

relative_url: Pattern = re_compile(r"^(?:https?://(?:www\.)?furaffinity\.net)?(.*)")
mentions_regexp: Pattern = re_compile(r"^(?:(?:https?://)?(?:www\.)?furaffinity\.net)?/user/([^/#]+).*$")
watchlist_next_regexp: Pattern = re_compile(r"/watchlist/(?:by|to)/[^/]+/(\d+)")
not_found_messages: tuple[str, ...] = ("not in our database", "cannot be found", "could not be found", "user not found")
deactivated_messages: tuple[str, ...] = ("deactivated", "pending deletion")
smilie_icons: tuple[str, ...] = (
    "crying", "derp", "dunno", "embarrassed", "evil", "gift", "huh", "lmao", "love", "nerd", "note", "oooh", "pleased",
    "rollingeyes", "sad", "sarcastic", "serious", "sleepy", "smile", "teeth", "tongue", "veryhappy", "wink", "yelling",
    "zipped", "angel", "badhairday", "cd", "coffee", "cool", "whatever"
)


def get_attr(tag: Tag, attr: str) -> str:
    return value[0] if isinstance(value := tag.attrs[attr], list) else value


def parse_page(text: str) -> BeautifulSoup:
    return BeautifulSoup(text, "lxml")


def check_page_raise(page: BeautifulSoup) -> None:
    if page is None:
        raise NonePage
    elif not (title := page.title.text.lower() if page.title else ""):
        raise NoTitle
    elif title.startswith("account disabled"):
        raise DisabledAccount
    elif title == "system error":
        error_text: str = error.text if (error := page.select_one("div.section-body")) else ""
        if any(m in error_text.lower() for m in not_found_messages):
            raise NotFound
        else:
            raise ServerError(*filter(bool, map(str.strip, error_text.splitlines())))
    elif notice := page.select_one("section.notice-message"):
        notice_text: str = notice.text
        if any(m in notice_text.lower() for m in deactivated_messages):
            raise DisabledAccount
        elif any(m in notice_text.lower() for m in not_found_messages):
            raise NotFound
        else:
            raise NoticeMessage(*filter(bool, map(str.strip, notice_text.splitlines())))


def username_url(username: str) -> str:
    return sub(r"[^a-z\d.~-]", "", username.lower())


def inner_html(tag: Tag) -> str:
    return tag.decode_contents()


def clean_html(html: str) -> str:
    return sub(r" *(<br/?>) *", r"\1", minify(html, remove_comments=True, reduce_boolean_attributes=True)).strip()


def html_to_bbcode(html: str) -> str:
    body: Optional[Tag] = parse_page(f"<html><body>{html}</body></html>").select_one("html > body")
    if not body:
        return ""

    for linkusername in body.select("a.linkusername"):
        linkusername.replaceWith(f"@{linkusername.text.strip()}")

    for iconusername in body.select("a.iconusername,a.usernameicon"):
        username: str = iconusername.text.strip() or iconusername.attrs.get('href', '').strip('/').split('/')[-1]
        if icon := iconusername.select_one("img"):
            username = icon.attrs.get('alt', '').strip() or username
        iconusername.replaceWith(f":icon{username}:" if iconusername.text.strip() else f":{username}icon:")

    for img in body.select("img"):
        img.replaceWith(f"[img={img.attrs.get('src', '')}/]")

    for hr in body.select("hr"):
        hr.replaceWith("-----")

    for smilie in body.select("i.smilie"):
        smilie_class: list[str] = list(smilie.attrs.get("class", []))
        smilie_name: str = next(filter(lambda c: c not in ["smilie", ""], smilie_class), "")
        smilie.replaceWith(f":{smilie_name or 'smilie'}:")

    for span in body.select("span.bbcode[style*=color]"):
        if m := match(r".*color: ?([^ ;]+).*", span.attrs["style"]):
            span.replaceWith(f"[color={m[1]}]", *span.children, "[/color]")
        else:
            span.replaceWith(*span.children)

    for nav_link in body.select("span.parsed_nav_links"):
        a_tags = nav_link.select("a")
        a_prev_tag: Optional[Tag] = next((a for a in a_tags if "prev" in a.text.lower()), None)
        a_frst_tag: Optional[Tag] = next((a for a in a_tags if "first" in a.text.lower()), None)
        a_next_tag: Optional[Tag] = next((a for a in a_tags if "next" in a.text.lower()), None)
        a_prev = a_prev_tag.attrs.get("href", "").strip("/").split("/")[-1] if a_prev_tag else ""
        a_frst = a_frst_tag.attrs.get("href", "").strip("/").split("/")[-1] if a_frst_tag else ""
        a_next = a_next_tag.attrs.get("href", "").strip("/").split("/")[-1] if a_next_tag else ""
        nav_link.replaceWith(f"[{a_prev or '-'},{a_frst or '-'},{a_next or '-'}]")

    for a in body.select("a.auto_link_shortened:not(.named_url), a.auto_link:not(.named_url)"):
        a.replaceWith(a.attrs.get('href', ''))

    for a in body.select("a"):
        href_match: Optional[Match] = relative_url.match(a.attrs.get('href', ''))
        a.replaceWith(f"[url={href_match[1] if href_match else a.attrs.get('href', '')}]",
                      *a.children,
                      "[/url]")

    for yt in body.select("iframe[src*='youtube.com/embed']"):
        yt.replaceWith(f"[yt]https://youtube.com/embed/{yt.attrs.get('src', '').strip('/').split('/')}[/yt]")

    for quote_name_tag in body.select("span.bbcode.bbcode_quote > span.bbcode_quote_name"):
        quote_author: str = quote_name_tag.text.strip().removesuffix('wrote:').strip()
        quote_tag = quote_name_tag.parent
        if not quote_tag:
            quote_name_tag.replaceWith(quote_author)
            continue
        quote_name_tag.decompose()
        quote_tag.replaceWith(f"[quote{('=' + quote_author) if quote_author else ''}]",
                              *quote_tag.children,
                              "[/quote]")

    for quote_tag in body.select("span.bbcode.bbcode_quote"):
        quote_tag.replaceWith("[quote]", *quote_tag.children, "[/quote]")

    for [selector, bbcode_tag] in (
            ("i", "i"),
            ("b", "b"),
            ("strong", "b"),
            ("u", "u"),
            ("s", "s"),
            ("code.bbcode_left", "left"),
            ("code.bbcode_center", "center"),
            ("code.bbcode_right", "right"),
            ("span.bbcode_spoiler", "spoiler"),
            ("sub", "sub"),
            ("sup", "sup"),
            ("h1", "h1"),
            ("h2", "h2"),
            ("h3", "h3"),
            ("h4", "h4"),
            ("h5", "h5"),
            ("h6", "h6"),
    ):
        for tag in body.select(selector):
            tag.replaceWith(f"[{bbcode_tag}]", *tag.children, f"[/{bbcode_tag}]")

    for br in body.select("br"):
        br.replaceWith("\n")

    for p in body.select("p"):
        p.replaceWith(*p.children)

    for tag in body.select("*"):
        if not (div_class := tag.attrs.get("class", None)):
            tag.replaceWith(f"[tag={tag.name}]", *tag.children, "[/tag.{tag.name}]")
        else:
            tag.replaceWith(f"[tag={tag.name}.{' '.join(div_class) if isinstance(div_class, list) else div_class}]",
                            *tag.children,
                            "[/tag]")

    bbcode: str = body.decode_contents()

    bbcode = sub(" *$", "", bbcode, flags=MULTILINE)
    bbcode = sub("^ *", "", bbcode, flags=MULTILINE)

    for char, substitution in (
            ("©", "(c)"),
            ("™", "(tm)"),
            ("®", "(r)"),
            ("&copy;", "(c)"),
            ("&reg;", "(tm)"),
            ("&trade;", "(r)"),
            ("&lt;", "<"),
            ("&gt;", ">"),
            ("&amp;", "&"),
    ):
        bbcode = bbcode.replace(char, substitution)

    return bbcode.strip(" ")


def bbcode_to_html(bbcode: str) -> str:
    def render_url(_tag_name, value: str, options: dict[str, str], _parent, _context) -> str:
        return f'<a class="auto_link named_url" href="{options.get("url", "#")}">{value}</a>'

    def render_color(_tag_name, value, options, _parent, _context) -> str:
        return f'<span class=bbcode style="color:{options.get("color", "inherit")};">{value}</span>'

    def render_quote(_tag_name, value: str, options: dict[str, str], _parent, _context) -> str:
        author: str = options.get("quote", "")
        author = f"<span class=bbcode_quote_name>{author} wrote:</span>" if author else ""
        return f'<span class="bbcode bbcode_quote">{author}{value}</span>'

    def render_tags(tag_name: str, value: str, options: dict[str, str], _parent, _context) -> str:
        if not options and tag_name.islower():
            return f"<{tag_name}>{value}</{tag_name}>"
        return f"[{tag_name} {' '.join(f'{k}={v}' if v else k for k, v in options.items())}]{value}"

    def render_tag(_tag_name, value: str, options: dict[str, str], _parent, _context) -> str:
        name, *classes = options["tag"].split(".")
        return f'<{name} class="{" ".join(classes)}">{value}</{name}>'

    def parse_extra(page: BeautifulSoup) -> BeautifulSoup:
        child: NavigableString
        child_new: Tag
        has_match: bool = True
        while has_match:
            has_match = False
            for child in [c for e in page.select("*:not(a)") for c in e.children if isinstance(c, NavigableString)]:
                if m_ := match(rf"(.*):({'|'.join(smilie_icons)}):(.*)", child):
                    has_match = True
                    child_new = Tag(name="i", attrs={"class": f"smilie {m_[2]}"})
                    child.replaceWith(m_[1], child_new, m_[3])
                elif m_ := match(r"(.*)(?:@([a-zA-Z0-9.~_-]+)|:link([a-zA-Z0-9.~_-]+):)(.*)", child):
                    has_match = True
                    child_new = Tag(name="a", attrs={"class": "linkusername", "href": f"/user/{m_[2] or m_[3]}"})
                    child_new.insert(0, m_[2] or m_[3])
                    child.replaceWith(m_[1], child_new, m_[4])
                elif m_ := match(r"(.*):(?:icon([a-zA-Z0-9.~_-]+)|([a-zA-Z0-9.~_-]+)icon):(.*)", child):
                    has_match = True
                    user: str = m_[2] or m_[3] or ""
                    child_new = Tag(name="a", attrs={"class": "iconusername", "href": f"/user/{user}"})
                    child_new_img: Tag = Tag(name="img",
                                             attrs={"alt": user, "title": user,
                                                    "src": f"//a.furaffinity.net/{datetime.now():%Y%m%d}/{user}.gif"})
                    child_new.insert(0, child_new_img)
                    if m_[2]:
                        child_new.insert(1, f"\xA0{m_[2]}")
                    child.replaceWith(m_[1], child_new, m_[4])
                elif m_ := match(r"(.*)\[ *(?:(\d+)|-)?, *(?:(\d+)|-)? *, *(?:(\d+)|-)? *](.*)", child):
                    has_match = True
                    child_new = Tag(name="span", attrs={"class": "parsed_nav_links"})
                    child_new_1: Union[Tag, str] = "<<<\xA0PREV"
                    child_new_2: Union[Tag, str] = "FIRST"
                    child_new_3: Union[Tag, str] = "NEXT\xA0>>>"
                    if m_[2]:
                        child_new_1 = Tag(name="a", attrs={"href": f"/view/{m_[2]}"})
                        child_new_1.insert(0, "<<<\xA0PREV")
                    if m_[3]:
                        child_new_2 = Tag(name="a", attrs={"href": f"/view/{m_[3]}"})
                        child_new_2.insert(0, "<<<\xA0FIRST")
                    if m_[4]:
                        child_new_3 = Tag(name="a", attrs={"href": f"/view/{m_[4]}"})
                        child_new_3.insert(0, "NEXT\xA0>>>")
                    child_new.insert(0, child_new_1)
                    child_new.insert(1, "\xA0|\xA0")
                    child_new.insert(2, child_new_2)
                    child_new.insert(3, "\xA0|\xA0")
                    child_new.insert(4, child_new_3)
                    child.replaceWith(m_[1], child_new, m_[5])

        for p in page.select("p"):
            p.replaceWith(*p.children)

        return page

    parser: BBCodeParser = BBCodeParser(install_defaults=False, replace_links=False, replace_cosmetic=True)
    parser.REPLACE_ESCAPE = (
        ("&", "&amp;"),
        ("<", "&lt;"),
        (">", "&gt;"),
    )
    parser.REPLACE_COSMETIC = (
        ("(c)", "&copy;"),
        ("(r)", "&reg;"),
        ("(tm)", "&trade;"),
    )

    for tag in ("i", "b", "u", "s", "sub", "sup", "h1", "h2", "h3", "h3", "h4", "h5", "h6"):
        parser.add_formatter(tag, render_tags)
    for align in ("left", "center", "right"):
        parser.add_simple_formatter(align, f'<code class="bbcode bbcode_{align}">%(value)s</code>')

    parser.add_simple_formatter("spoiler", '<span class="bbcode bbcode_spoiler">%(value)s</span>')
    parser.add_simple_formatter("url", '<a class="auto_link named_link">%(value)s</a>')
    parser.add_simple_formatter(
        "iconusername",
        f'<a class=iconusername href="/user/%(value)s">'
        f'<img alt="%(value)s" title="%(value)s" src="//a.furaffinity.net/{datetime.now():%Y%m%d}/%(value)s.gif">'
        f'%(value)s'
        f'</a>'
    )
    parser.add_simple_formatter(
        "usernameicon",
        f'<a class=iconusername href="/user/%(value)s">'
        f'<img alt="%(value)s" title="%(value)s" src="//a.furaffinity.net/{datetime.now():%Y%m%d}/%(value)s.gif">'
        f'</a>'
    )
    parser.add_simple_formatter("linkusername", '<a class=linkusername href="/user/%(value)s">%(value)s</a>')
    parser.add_simple_formatter("hr", "<hr>", standalone=True)

    parser.add_formatter("url", render_url)
    parser.add_formatter("color", render_color)
    parser.add_formatter("quote", render_quote)
    parser.add_formatter("tag", render_tag)

    bbcode = sub(r"-{5,}", "[hr]", bbcode)

    result_page: BeautifulSoup = parse_extra(parse_page(parser.format(bbcode)))
    return (result_page.select_one("html > body") or result_page).decode_contents()


def parse_mentions(tag: Tag) -> list[str]:
    mentions: list[str] = [username_url(m[1]) for a in tag.select("a")
                           if (m := match(mentions_regexp, get_attr(a, "href")))]
    return sorted(set([m for m in mentions if m]), key=mentions.index)


def parse_loggedin_user(page: BeautifulSoup) -> Optional[str]:
    return get_attr(avatar, "alt") if (avatar := page.select_one("img.loggedin_user_avatar")) else None


def parse_journal_section(section_tag: Tag) -> dict[str, Any]:
    id_: int = int(section_tag.attrs.get("id", "00000")[4:])
    tag_title: Optional[Tag] = section_tag.select_one("h2")
    tag_date: Optional[Tag] = section_tag.select_one("span.popup_date")
    tag_content: Optional[Tag] = section_tag.select_one("div.journal-body")
    tag_comments: Optional[Tag] = section_tag.select_one("div.section-footer > a > span")

    assert id_ != 0, _raise_exception(ParsingError("Missing ID"))
    assert tag_title is not None, _raise_exception(ParsingError("Missing title tag"))
    assert tag_date is not None, _raise_exception(ParsingError("Missing date tag"))
    assert tag_content is not None, _raise_exception(ParsingError("Missing content tag"))
    assert tag_comments is not None, _raise_exception(ParsingError("Missing comments tag"))

    # noinspection DuplicatedCode
    title: str = tag_title.text.strip()
    date: datetime = parse_date(
        get_attr(tag_date, "title").strip()
        if match(r"^[A-Za-z]+ \d+,.*$", get_attr(tag_date, "title"))
        else tag_date.text.strip()
    )
    content: str = clean_html(inner_html(tag_content))
    mentions: list[str] = parse_mentions(tag_content)
    comments: int = int(tag_comments.text.strip())

    return {
        "id": id_,
        "title": title,
        "date": date,
        "content": content,
        "mentions": mentions,
        "comments": comments,
    }


def parse_journal_page(journal_page: BeautifulSoup) -> dict[str, Any]:
    user_info: dict[str, str] = parse_user_folder(journal_page)
    tag_id: Optional[Tag] = journal_page.select_one("meta[property='og:url']")
    tag_title: Optional[Tag] = journal_page.select_one("h2.journal-title")
    tag_date: Optional[Tag] = journal_page.select_one("span.popup_date")
    tag_header: Optional[Tag] = journal_page.select_one("div.journal-header")
    tag_footer: Optional[Tag] = journal_page.select_one("div.journal-footer")
    tag_content: Optional[Tag] = journal_page.select_one("div.journal-content")
    tag_comments: Optional[Tag] = journal_page.select_one("div.section-footer > span")

    assert tag_id is not None, _raise_exception(ParsingError("Missing ID tag"))
    assert tag_title is not None, _raise_exception(ParsingError("Missing title tag"))
    assert tag_date is not None, _raise_exception(ParsingError("Missing date tag"))
    assert tag_content is not None, _raise_exception(ParsingError("Missing content tag"))
    assert tag_comments is not None, _raise_exception(ParsingError("Missing comments tag"))

    id_: int = int(tag_id.attrs.get("content", "0").strip("/").split("/")[-1])
    # noinspection DuplicatedCode
    title: str = tag_title.text.strip()
    date: datetime = parse_date(
        get_attr(tag_date, "title").strip()
        if match(r"^[A-Za-z]+ \d+,.*$", get_attr(tag_date, "title"))
        else tag_date.text.strip()
    )
    header: str = clean_html(inner_html(tag_header)) if tag_header else ""
    footer: str = clean_html(inner_html(tag_footer)) if tag_footer else ""
    content: str = clean_html(inner_html(tag_content))
    mentions: list[str] = parse_mentions(tag_content)
    comments: int = int(tag_comments.text.strip())

    assert id_ != 0, _raise_exception(ParsingError("Missing ID"))

    return {
        **user_info,
        "id": id_,
        "title": title,
        "date": date,
        "content": content,
        "header": header,
        "footer": footer,
        "mentions": mentions,
        "comments": comments,
    }


def parse_submission_figure(figure_tag: Tag) -> dict[str, Any]:
    id_: int = int(get_attr(figure_tag, "id")[4:])
    tag_title: Optional[Tag] = figure_tag.select_one("figcaption a[href^='/view/']")
    tag_author: Optional[Tag] = figure_tag.select_one("figcaption a[href^='/user/']")
    tag_thumbnail: Optional[Tag] = figure_tag.select_one("img")

    assert tag_title is not None, _raise_exception(ParsingError("Missing title tag"))
    assert tag_author is not None, _raise_exception(ParsingError("Missing author tag"))
    assert tag_thumbnail is not None, _raise_exception(ParsingError("Missing thumbnail tag"))

    title: str = get_attr(tag_title, "title")
    author: str = get_attr(tag_author, "title")
    rating: str = next(c for c in figure_tag["class"] if c.startswith("r-"))[2:]
    type_: str = next(c for c in figure_tag["class"] if c.startswith("t-"))[2:]
    thumbnail_url: str = "https:" + get_attr(tag_thumbnail, "src")

    return {
        "id": id_,
        "title": title,
        "author": author,
        "rating": rating,
        "type": type_,
        "thumbnail_url": thumbnail_url,
    }


def parse_submission_author(author_tag: Tag) -> dict[str, Any]:
    tag_author: Optional[Tag] = author_tag.select_one("div.submission-id-sub-container")

    assert tag_author is not None, _raise_exception(ParsingError("Missing author tag"))

    tag_author_name: Optional[Tag] = tag_author.select_one("a > strong")
    tag_author_icon: Optional[Tag] = author_tag.select_one("img.submission-user-icon")

    assert tag_author_name is not None, _raise_exception(ParsingError("Missing author name tag"))
    assert tag_author_icon is not None, _raise_exception(ParsingError("Missing author icon tag"))

    author_name: str = tag_author_name.text.strip()
    author_title: str = ([*filter(bool, [child.strip()
                                         for child in tag_author.children
                                         if isinstance(child, NavigableString)][3:])] or [""])[-1]
    author_title = author_title if tag_author.select_one('a[href$="/#tip"]') is None else sub(r"\|$", "", author_title)
    author_title = author_title.strip("\xA0 ")  # NBSP
    author_icon_url: str = "https:" + get_attr(tag_author_icon, "src")

    return {
        "author": author_name,
        "author_title": author_title,
        "author_icon_url": author_icon_url,
    }


def parse_submission_page(sub_page: BeautifulSoup) -> dict[str, Any]:
    tag_id: Optional[Tag] = sub_page.select_one("meta[property='og:url']")
    tag_sub_info: Optional[Tag] = sub_page.select_one("div.submission-id-sub-container")

    assert tag_sub_info is not None, _raise_exception(ParsingError("Missing info tag"))

    tag_title: Optional[Tag] = tag_sub_info.select_one("div.submission-title")
    tag_author: Optional[Tag] = sub_page.select_one("div.submission-id-container")
    tag_date: Optional[Tag] = sub_page.select_one("span.popup_date")
    tag_tags: list[Tag] = sub_page.select("section.tags-row a")
    tag_views: Optional[Tag] = sub_page.select_one("div.views span")
    tag_comment_count: Optional[Tag] = sub_page.select_one("section.stats-container div.comments span")
    tag_favorites: Optional[Tag] = sub_page.select_one("div.favorites span")
    tag_rating: Optional[Tag] = sub_page.select_one("div.rating span")
    tag_type: Optional[Tag] = sub_page.select_one("div#submission_page[class^='page-content-type']")
    tag_fav: Optional[Tag] = sub_page.select_one("div.fav > a")
    tag_info: Optional[Tag] = sub_page.select_one("section.info.text")
    tag_user_folders: list[Tag] = sub_page.select("section.folder-list-container > div > a")

    assert tag_info is not None, _raise_exception(ParsingError("Missing info tag"))

    tag_category1: Optional[Tag] = tag_info.select_one("span.category-name")
    tag_category2: Optional[Tag] = tag_info.select_one("span.type-name")
    tag_species: Optional[Tag] = (info_spans := tag_info.select("span"))[2]
    tag_gender: Optional[Tag] = info_spans[3]
    tag_description: Optional[Tag] = sub_page.select_one("div.submission-description")
    tag_folder: Optional[Tag] = sub_page.select_one("a.button[href^='/scraps/'],a.button[href^='/gallery/']")
    tag_file_url: Optional[Tag] = sub_page.select_one("div.download a")
    tag_thumbnail_url: Optional[Tag] = sub_page.select_one("img#submissionImg")
    tag_prev: Optional[Tag] = sub_page.select_one("div.submission-content div.favorite-nav a:nth-child(1)")
    tag_next: Optional[Tag] = sub_page.select_one("div.submission-content div.favorite-nav a:last-child")

    assert tag_id is not None, _raise_exception(ParsingError("Missing id tag"))
    assert tag_title is not None, _raise_exception(ParsingError("Missing title tag"))
    assert tag_author is not None, _raise_exception(ParsingError("Missing author tag"))
    assert tag_date is not None, _raise_exception(ParsingError("Missing date tag"))
    assert tag_views is not None, _raise_exception(ParsingError("Missing views tag"))
    assert tag_comment_count is not None, _raise_exception(ParsingError("Missing comment count tag"))
    assert tag_favorites is not None, _raise_exception(ParsingError("Missing favorites tag"))
    assert tag_rating is not None, _raise_exception(ParsingError("Missing rating tag"))
    assert tag_type is not None, _raise_exception(ParsingError("Missing type tag"))
    assert tag_fav is not None, _raise_exception(ParsingError("Missing fav tag"))
    assert tag_category1 is not None, _raise_exception(ParsingError("Missing category1 tag"))
    assert tag_category2 is not None, _raise_exception(ParsingError("Missing category2 tag"))
    assert tag_species is not None, _raise_exception(ParsingError("Missing species tag"))
    assert tag_gender is not None, _raise_exception(ParsingError("Missing gender tag"))
    assert tag_description is not None, _raise_exception(ParsingError("Missing description tag"))
    assert tag_folder is not None, _raise_exception(ParsingError("Missing folder tag"))
    assert tag_file_url is not None, _raise_exception(ParsingError("Missing file URL tag"))
    assert tag_prev is not None, _raise_exception(ParsingError("Missing prev tag"))
    assert tag_next is not None, _raise_exception(ParsingError("Missing next tag"))

    tag_footer: Optional[Tag] = tag_description.select_one("div.submission-footer")

    id_: int = int(get_attr(tag_id, "content").strip("/").split("/")[-1])
    title: str = tag_title.text.strip()
    date: datetime = parse_date(
        get_attr(tag_date, "title").strip()
        if match(r"^[A-Za-z]+ \d+,.*$", get_attr(tag_date, "title"))
        else tag_date.text.strip()
    )
    tags: list[str] = [t.text.strip() for t in tag_tags]
    category: str = tag_category1.text.strip() + " / " + tag_category2.text.strip()
    species: str = tag_species.text.strip()
    gender: str = tag_gender.text.strip()
    rating: str = tag_rating.text.strip()
    views: int = int(tag_views.text.strip())
    comment_count: int = int(tag_comment_count.text.strip())
    favorites: int = int(tag_favorites.text.strip())
    type_: str = tag_type["class"][0][18:]
    footer: str = ""
    if tag_footer:
        if tag_footer_hr := tag_footer.select_one("hr"):
            tag_footer_hr.decompose()
        footer = clean_html(inner_html(tag_footer))
        tag_footer.decompose()
    description: str = clean_html(inner_html(tag_description))
    mentions: list[str] = parse_mentions(tag_description)
    folder: str = m.group(1).lower() if (m := match(r"^/(scraps|gallery)/.*$", get_attr(tag_folder, "href"))) else ""
    file_url: str = "https:" + get_attr(tag_file_url, "href")
    thumbnail_url: str = ("https:" + get_attr(tag_thumbnail_url, "data-preview-src")) if tag_thumbnail_url else ""
    prev_sub: Optional[int] = int(
        get_attr(tag_prev, "href").split("/")[-2]) if tag_prev and tag_prev.text.lower() == "prev" else None
    next_sub: Optional[int] = int(
        get_attr(tag_next, "href").split("/")[-2]) if tag_next and tag_next.text.lower() == "next" else None
    fav_link: Optional[str] = f"{root}{href}" if (href := get_attr(tag_fav, "href")).startswith("/fav/") else None
    unfav_link: Optional[str] = f"{root}{href}" if (href := get_attr(tag_fav, "href")).startswith("/unfav/") else None
    user_folders: list[tuple[str, str, str]] = []
    for a in tag_user_folders:
        tag_folder_name: Optional[Tag] = a.select_one("span")
        tag_folder_group: Optional[Tag] = a.select_one("strong")
        assert tag_folder_name is not None, _raise_exception(ParsingError("Missing folder name tag"))
        user_folders.append((
            tag_folder_name.text.strip(),
            (root + href) if (href := a.attrs.get("href", "")) else "",
            tag_folder_group.text.strip() if tag_folder_group else ""
        ))

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
        "views": views,
        "comment_count": comment_count,
        "favorites": favorites,
        "type": type_,
        "footer": footer,
        "description": description,
        "mentions": mentions,
        "folder": folder,
        "user_folders": user_folders,
        "file_url": file_url,
        "thumbnail_url": thumbnail_url,
        "prev": prev_sub,
        "next": next_sub,
        "fav_link": fav_link,
        "unfav_link": unfav_link,
    }


def parse_user_page(user_page: BeautifulSoup) -> dict[str, Any]:
    tag_status: Optional[Tag] = user_page.select_one("div.username h2")
    tag_profile: Optional[Tag] = user_page.select_one("div.userpage-profile")
    tag_title_join_date: Optional[Tag] = user_page.select_one("div.userpage-flex-item.username > span")
    tag_stats: Optional[Tag] = user_page.select_one("div.userpage-section-right div.table")
    tag_watchlist_to: Optional[Tag] = user_page.select_one("a[href*='watchlist/to']")
    tag_watchlist_by: Optional[Tag] = user_page.select_one("a[href*='watchlist/by']")
    tag_infos: list[Tag] = user_page.select("div#userpage-contact-item div.table-row")
    tag_contacts: list[Tag] = user_page.select("div#userpage-contact div.user-contact-user-info")
    tag_user_icon_url: Optional[Tag] = user_page.select_one("img.user-nav-avatar")
    tag_user_nav_controls: Optional[Tag] = user_page.select_one("div.user-nav-controls")

    assert tag_status is not None, _raise_exception(ParsingError("Missing name tag"))
    assert tag_profile is not None, _raise_exception(ParsingError("Missing profile tag"))
    assert tag_title_join_date is not None, _raise_exception(ParsingError("Missing join date tag"))
    assert tag_stats is not None, _raise_exception(ParsingError("Missing stats tag"))
    assert tag_watchlist_to is not None, _raise_exception(ParsingError("Missing watchlist to tag"))
    assert tag_watchlist_by is not None, _raise_exception(ParsingError("Missing watchlist by tag"))
    assert tag_user_icon_url is not None, _raise_exception(ParsingError("Missing user icon URL tag"))
    assert tag_user_nav_controls is not None, _raise_exception(ParsingError("Missing user nav controls tag"))

    tag_watch: Optional[Tag] = tag_user_nav_controls.select_one("a[href^='/watch/'], a[href^='/unwatch/']")
    tag_block: Optional[Tag] = tag_user_nav_controls.select_one("a[href^='/block/'], a[href^='/unblock/']")

    status: str = (u := tag_status.text.strip())[0]
    name: str = u[1:]
    title: str = ttd[0].strip() if len(ttd := tag_title_join_date.text.rsplit("|", 1)) > 1 else ""
    join_date: datetime = parse_date(ttd[-1].strip().split(":", 1)[1])
    profile: str = clean_html(inner_html(tag_profile))
    stats: tuple[int, ...] = (
        *map(lambda s: int(s.split(":")[1]), filter(bool, map(str.strip, tag_stats.text.split("\n")))),
        int(m[1]) if (m := search(r"(\d+)", tag_watchlist_to.text)) else 0,
        int(m[1]) if (m := search(r"(\d+)", tag_watchlist_by.text)) else 0,
    )

    tag_key: Optional[Tag]
    info: dict[str, str] = {}
    contacts: dict[str, str] = {}
    for tb in tag_infos:
        if (tag_key := tb.select_one("div")) is None:
            continue
        elif "profile-empty" in tb.attrs.get("class", []):
            continue
        elif not (val := [*filter(bool, [c.strip() for c in tb.children if isinstance(c, NavigableString)])][-1:]):
            continue
        info[tag_key.text.strip()] = val[0]
    for pc in tag_contacts:
        if (tag_key := pc.select_one("span")) is None:
            continue
        contacts[tag_key.text.strip()] = get_attr(a, "href") if (a := pc.select_one("a")) else \
            [*filter(bool, map(str.strip, pc.text.split("\n")))][-1]
    user_icon_url: str = "https:" + get_attr(tag_user_icon_url, "src")
    tag_watch_href: str = get_attr(tag_watch, "href") if tag_watch else ""
    watch: Optional[str] = f"{root}{tag_watch_href}" if tag_watch_href.startswith("/watch/") else None
    unwatch: Optional[str] = f"{root}{tag_watch_href}" if tag_watch_href.startswith("/unwatch/") else None
    tag_block_href: str = get_attr(tag_block, "href") if tag_block else ""
    block: Optional[str] = f"{root}{tag_block_href}" if tag_block_href.startswith("/block/") else None
    unblock: Optional[str] = f"{root}{tag_block_href}" if tag_block_href.startswith("/unblock/") else None

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
        "watch": watch,
        "unwatch": unwatch,
        "block": block,
        "unblock": unblock,
    }


def parse_comment_tag(tag: Tag) -> dict:
    tag_id: Optional[Tag] = tag.select_one("a")
    tag_username: Optional[Tag] = tag.select_one("div.header strong.comment_username > h3")
    tag_user_icon: Optional[Tag] = tag.select_one("div.header img.comment_useravatar")
    tag_user_title: Optional[Tag] = tag.select_one("div.header div.name div.cell span.hideonmobile")
    tag_body: Optional[Tag] = tag.select_one("div.base > div.body")
    tag_parent_link: Optional[Tag] = tag.select_one("a.comment-parent")
    tag_edited: Optional[Tag] = tag.select_one("img.edited")

    assert tag_id is not None, _raise_exception(ParsingError("Missing link tag"))
    assert tag_body is not None, _raise_exception(ParsingError("Missing body tag"))

    attr_id: Optional[str] = tag_id.attrs.get("id")

    assert attr_id is not None, _raise_exception(ParsingError("Missing id attribute"))

    comment_id: int = int(attr_id.removeprefix("cid:"))
    comment_text: str = clean_html(inner_html(tag_body))

    if tag_username is None:
        return {
            "id": comment_id,
            "user_name": "",
            "user_title": "",
            "user_icon_url": "",
            "timestamp": 0,
            "text": comment_text,
            "parent": None,
            "edited": tag_edited is not None,
            "hidden": True,
        }

    assert tag_username is not None, _raise_exception(ParsingError("Missing user name tag"))
    assert tag_user_icon is not None, _raise_exception(ParsingError("Missing user icon tag"))
    assert tag_user_title is not None, _raise_exception(ParsingError("Missing user title tag"))

    attr_timestamp: Optional[str] = tag.attrs.get("data-timestamp")
    attr_user_icon: Optional[str] = tag_user_icon.attrs.get("src")
    attr_parent_href: Optional[str] = tag_parent_link.attrs.get("href") if tag_parent_link is not None else None

    assert attr_timestamp is not None, _raise_exception(ParsingError("Missing timestamp attribute"))
    assert attr_user_icon is not None, _raise_exception(ParsingError("Missing user icon src attribute"))

    parent_id: Optional[int] = int(attr_parent_href.removeprefix("#cid:")) if attr_parent_href else None

    return {
        "id": comment_id,
        "user_name": tag_username.text.strip(),
        "user_title": tag_user_title.text.strip(),
        "user_icon_url": "https:" + attr_user_icon,
        "timestamp": int(attr_timestamp),
        "text": comment_text,
        "parent": parent_id,
        "edited": tag_edited is not None,
        "hidden": False,
    }


def parse_comments(page: BeautifulSoup) -> list[Tag]:
    return page.select("div.comment_container")


def parse_user_tag(user_tag: Tag) -> dict[str, Any]:
    status: str = (u := [*filter(bool, map(str.strip, user_tag.text.split("\n")))])[0][0]
    name: str = u[0][1:]
    title: str = ttd[0].strip() if len(ttd := u[1].rsplit("|", 1)) > 1 else ""
    join_date: datetime = parse_date(ttd[-1].strip().split(":", 1)[1])

    return {
        "user_name": name,
        "user_status": status,
        "user_title": title,
        "user_join_date": join_date,
    }


def parse_user_folder(folder_page: BeautifulSoup) -> dict[str, Any]:
    tag_username: Optional[Tag] = folder_page.select_one("div.userpage-flex-item.username")
    tag_user_icon: Optional[Tag] = folder_page.select_one("img.user-nav-avatar")
    assert tag_username is not None, _raise_exception(ParsingError("Missing username tag"))
    assert tag_user_icon is not None, _raise_exception(ParsingError("Missing user icon tag"))
    return {
        **parse_user_tag(tag_username),
        "user_icon_url": "https:" + get_attr(tag_user_icon, "src"),
    }


def parse_submission_figures(figures_page: BeautifulSoup) -> list[Tag]:
    return figures_page.select("figure[id^='sid-']")


def parse_user_submissions(submissions_page: BeautifulSoup) -> dict[str, Any]:
    user_info: dict[str, str] = parse_user_folder(submissions_page)
    last_page: bool = not any(b.text.lower() == "next" for b in submissions_page.select("form button.button"))

    return {
        **user_info,
        "figures": parse_submission_figures(submissions_page),
        "last_page": last_page,
    }


def parse_user_favorites(favorites_page: BeautifulSoup) -> dict[str, Any]:
    parsed_submissions = parse_user_submissions(favorites_page)
    tag_next_page: Optional[Tag] = favorites_page.select_one("a[class~=button][class~=standard][class~=right]")
    next_page: str = get_attr(tag_next_page, "href").split("/", 3)[-1] if tag_next_page else ""

    return {
        **parsed_submissions,
        "next_page": next_page,
    }


def parse_user_journals(journals_page: BeautifulSoup) -> dict[str, Any]:
    user_info: dict[str, str] = parse_user_folder(journals_page)
    sections: list[Tag] = journals_page.select("section[id^='jid:']")
    next_page_tag: Optional[Tag] = journals_page.select_one("div.mini-nav > div.mini-nav-cell:first-child > a.button")

    return {
        **user_info,
        "sections": sections,
        "last_page": next_page_tag is None,
    }


def parse_watchlist(watch_page: BeautifulSoup) -> tuple[list[tuple[str, str]], int]:
    tags_users: list[Tag] = watch_page.select("div.watch-list-items")
    tag_next: Optional[Tag] = watch_page.select_one("section div.floatright form[method=get]")
    match_next: Optional[Match] = watchlist_next_regexp.match(get_attr(tag_next, "action")) if tag_next else None
    return (
        [((u := t.text.strip().replace(" ", ""))[0], u[1:]) for t in tags_users],
        int(match_next[1]) if match_next else 0,
    )
