<div align="center">

<img alt="logo" width="400" src="https://gitlab.com/uploads/-/system/project/avatar/7434083/logo.png">

# Fur Affinity API

Python library to implement API-like functionality for the [Fur Affinity](https://furaffinity.net) website.

[![version_pypi](https://img.shields.io/pypi/v/faapi?logo=pypi)](https://pypi.org/project/faapi/)
[![version_gitlab](https://img.shields.io/gitlab/v/tag/MatteoCampinoti94/faapi?label=version&sort=date&logo=gitlab&color=FCA121)](https://gitlab.com/MatteoCampinoti94/faapi)
[![pipeline status](https://gitlab.com/MatteoCampinoti94/FAAPI/badges/master/pipeline.svg)](https://gitlab.com/MatteoCampinoti94/FAAPI/-/commits/master)
[![version_python](https://img.shields.io/pypi/pyversions/faapi?logo=Python)](https://www.python.org)

[![issues_gitlab](https://img.shields.io/badge/dynamic/json?logo=gitlab&color=orange&label=issues&suffix=%20open&query=%24.length&url=https%3A%2F%2Fgitlab.com%2Fapi%2Fv4%2Fprojects%2Fmatteocampinoti94%252Ffaapi%2Fissues%3Fstate%3Dopened)](https://gitlab.com/MatteoCampinoti94/FAAPI/issues)
[![issues_github](https://img.shields.io/github/issues/matteocampinoti94/faapi?logo=github&color=blue)](https://github.com/MatteoCampinoti94/FAAPI/issues)

</div>

## Requirements

Python 3.9+ is necessary to run this library. [Poetry](https://python-poetry.org) is used for packaging and dependency management.

## Usage

The API comprises a main class `FAAPI`, two submission classes `Submission` and `SubmissionPartial`, a journal
class `Journal`, and a user class `User`.

Once `FAAPI` is initialized, its methods can be used to crawl FA and return parsed objects.

```python
from requests.cookies import RequestsCookieJar
import faapi
import orjson

cookies = RequestsCookieJar()
cookies.set("a", "38565475-3421-3f21-7f63-3d341339737")
cookies.set("b", "356f5962-5a60-0922-1c11-65003b703038")

api = faapi.FAAPI(cookies)
sub, sub_file = api.submission(12345678, get_file=True)

print(sub.id, sub.title, sub.author, f"{len(sub_file) / 1024:02f}KiB")

with open(f"{sub.id}.json", "wb") as f:
    f.write(orjson.dumps(dict(sub)))

with open(sub.file_url.split("/")[-1], "wb") as f:
    f.write(sub_file)

gallery, _ = api.gallery("user_name", 1)
with open("user_name-gallery.json", "wb") as f:
    f.write(orjson.dumps(list(map(dict, gallery))))
```

### robots.txt

At init, the `FAAPI` object downloads the [robots.txt](https://www.furaffinity.net/robots.txt) file from FA to determine
the `Crawl-delay` and `disallow` values set therein. If not set in the robots.txt file, a crawl delay value of 1 second
is used.

To respect this value, the default behaviour of the `FAAPI` object is to wait when a get request is made if the last
request was performed more recently then the crawl delay value.

See under [FAAPI](#faapi) for more details on this behaviour.

Furthermore, any get operation that points to a disallowed path from robots.txt will raise an exception. This check
should not be circumvented, and the developer of this library does not take responsibility for violations of the TOS of
Fur Affinity.

### Cookies

To access protected pages, cookies from an active session are needed. These cookies can be given to the FAAPI object as
a list of dictionaries - each containing a `name` and a `value` field -, or as a `http.cookiejar.CookieJar`
object (`requests.cookies.RequestsCookieJar` and other objects inheriting from `CookieJar` are also supported). The
cookies list should look like the following example:

```python
cookies = [
    {"name": "a", "value": "38565475-3421-3f21-7f63-3d3413397537"},
    {"name": "b", "value": "356f5962-5a60-0922-1c11-65003b703038"},
]
```

```python
from requests.cookies import RequestsCookieJar

cookies = RequestsCookieJar()
cookies.set("a", "38565475-3421-3f21-7f63-3d3413397537")
cookies.set("b", "356f5962-5a60-0922-1c11-65003b703038")
```

To access session cookies, consult the manual of the browser used to log in.

*Note:* it is important to not logout of the session the cookies belong to, otherwise they will no longer work.
*Note:* as of 2021-12-05 only cookies `a` and `b` are needed.

### User Agent

`FAAPI` attaches a `User-Agent` header to every request. The user agent string is generated at startup in the following
format: `faapi/{library version} Python/{python version} {system name}/{system release}`.

## Objects

### FAAPI

This is the main object that handles all the calls to scrape pages and get submissions.

It holds 6 different fields:

* `session: CloudflareScraper` `cfscrape` session used for get requests
* `robots: urllib.robotparser.RobotFileParser` robots.txt handler
* `user_agent: str` user agent used by the session (property, cannot be set)
* `crawl_delay: float` crawl delay from robots.txt (property, cannot be set)
* `last_get: float` time of last get (UNIX time)
* `raise_for_unauthorized: bool = True` if set to `True`, raises an exception if a request is made and the resulting
  page is not from a login session

#### Init

`__init__(cookies: List[dict] | CookieJar = None)`

The class init has a single optional argument `cookies` necessary to read logged-in-only pages. The cookies can be
omitted, and the API will still be able to access public pages.

*Note:* Cookies must be in the format mentioned above in [#Cookies](#cookies).

#### Methods & Properties

* `load_cookies(cookies: List[dict] | CookieJar)`<br>
  Load new cookies and create a new session.<br>
  *Note:* This method removes any cookies currently in use, to update/add single cookies access them from the session
  object.
* `handle_delay()`<br>
  Handles the crawl delay as set in the robots.txt
* `check_path(path: str, *, raise_for_disallowed: bool = False) -> bool`<br>
  Checks whether a given path is allowed by the robots.txt. If `raise_for_disallowed` is set to `True`
  a `DisallowedPath` exception is raised on non-allowed paths.
* `connection_status -> bool`<br>
  Returns the status of the connection.
* `login_status -> bool`<br>
  Returns the login status.
* `get(path: str, **params) -> requests.Response`<br>
  This returns a response object containing the result of the get operation on the given URL with the
  optional `**params` added to it (url provided is considered as path from 'https://www.furaffinity.net/').
* `get_parsed(path: str, *, skip_page_check: bool = False, skip_auth_check: bool = False, **params) -> bs4.BeautifulSoup`<br>
  Similar to `get()` but returns the parsed HTML from the normal get operation. If the GET request encountered an error,
  an `HTTPError` exception is raised. If `skip_page_check` is set to `True`, the parsed page is not checked for errors (
  e.g. non-existing submission). If `skip_auth_check` is set to `True`, the page is not checked for login status.
* `me() -> Optional[User]`<br>
  Returns the logged-in user as a `User` object if the cookies are from a login session.
* `submission(submission_id: int, get_file: bool = False, *, chunk_size: int = None) -> Tuple[Submission, Optional[bytes]]`<br>
  Given a submission ID, it returns a `Submission` object containing the various metadata of the submission itself and
  a `bytes` object with the submission file if `get_file` is passed as `True`. The optional `chunk_size` argument is
  used for the request; if left to `None` or set to 0 the download is performed directly without streaming.<br>
  *Note:* the author `UserPartial` object of the submission does not contain the `join_date` field as it does not appear
  on submission pages.
* `submission_file(submission: Submission, *, chunk_size: int = None) -> bytes`<br>
  Given a submission object, it downloads its file and returns it as a `bytes` object. The optional `chunk_size`
  argument is used for the request; if left to `None` or set to 0 the download is performed directly without streaming.
* `journal(journal_id: int) -> Journal`<br>
  Given a journal ID, it returns a `Journal` object containing the various metadata of the journal.
* `user(user: str) -> User`<br>
  Given a username, it returns a `User` object containing information regarding the user.
* `gallery(user: str, page: int = 1) -> Tuple[List[SubmissionPartial], int]`<br>
  Returns the list of submissions found on a specific gallery page, and the number of the next page. The returned page
  number is set to 0 if it is the last page.
* `scraps(user: str, page: int = 1) -> -> Tuple[List[SubmissionPartial], int]`<br>
  Returns the list of submissions found on a specific scraps page, and the number of the next page. The returned page
  number is set to 0 if it is the last page.
* `favorites(user: str, page: str = "") -> Tuple[List[SubmissionPartial], str]`<br>
  Downloads a user's favorites page. Because of how favorites pages work on FA, the `page` argument (and the one
  returned) are strings. If the favorites page is the last then an empty string is returned as next page. An empty page
  value as argument is equivalent to page 1.<br>
  *Note:* favorites page "numbers" do not follow any scheme and are only generated server-side.
* `journals(user: str, page: int = 1) -> -> Tuple[List[Journal], int]`<br>
  Returns the list of submissions found on a specific journals page, and the number of the next page. The returned page
  number is set to 0 if it is the last page.
* `search(q: str = "", page: int = 0, **params) -> Tuple[List[SubmissionPartial], int, int, int, int]`<br>
  Parses FA search given the query (and optional other params) and returns the submissions found, and the next page
  together with basic search statistics: the number of the first submission in the page (0-indexed), the number of the
  last submission in the page (0-indexed), and the total number of submissions found in the search. For example if the
  last three returned integers are 0, 47 and 437, then the page contains submissions 1 through 48 of a search that has
  found a total of 437 submissions.<br>
  *Note:* as of April 2021 the "/search" path is disallowed by Fur Affinity's robots.txt.
* `watchlist_to(self, user: str) -> List[User]`<br>
  Given a username, returns a list of `User` objects for each user that is watching the given user.
* `watchlist_by(self, user: str) -> List[User]`<br>
  Given a username, returns a list of `User` objects for each user that is watched by the given user.
* `user_exists(user: str) -> int`<br>
  Checks if the passed user exists - i.e. if there is a page under that name - and returns an int result.
    * 0 okay
    * 1 account disabled
    * 2 system error
    * 3 unknown error
    * 4 request error
* `submission_exists(submission_id: int) -> int`<br>
  Checks if the passed submissions exists - i.e. if there is a page with that ID - and returns an int result.
    * 0 okay
    * 1 account disabled
    * 2 system error
    * 3 unknown error
    * 4 request error
* `journal_exists(journal_id: int) -> int`<br>
  Checks if the passed journal exists - i.e. if there is a page under that ID - and returns an int result.
    * 0 okay
    * 1 account disabled
    * 2 system error
    * 3 unknown error
    * 4 request error

### Journal

This object contains information gathered when parsing a journals page, or a specific journal page. It contains the
following fields:

* `id: int` journal id
* `title: str` journal title
* `date: datetime` upload date as a [`datetime` object](https://docs.python.org/3/library/datetime.html) (defaults to
  timestamp 0)
* `author: UserPartial` journal author (filled only if the journal is parsed from a `bs4.BeautifulSoup` page)
* `content: str` journal content in HTML format
* `mentions: List[str]` the users mentioned in the content (if they were mentioned as links, e.g. `:iconusername:`,
  `@username`, etc.)
* `user_icon_url: str` the URL to the user icon (cannot be parsed when downloading via `FAAPI.get_journals`)
* `journal_item: Union[bs4.element.Tag, bs4.BeautifulSoup]` the journal tag/page used to parse the object fields

`Journal` objects can be directly cast to a dict object or iterated through.

#### Init

`__init__(journal_item: Union[bs4.element.Tag, bs4.BeautifulSoup] = None)`

`Journal` takes one optional parameters: a journal section tag from a journals page, or a parsed journal page. Parsing
is then performed based on the class of the passed object.

#### Methods

* `url -> str`<br>
  Property method that returns the Fur Affinity URL to the journal (`https://www.furaffinity.net/journal/{id}`).
* `parse(journal_item: Union[bs4.element.Tag, bs4.BeautifulSoup] = None)`<br>
  Parses the stored journal tag/page for information. If `journal_item` is passed, it overwrites the
  existing `journal_item` value.

### SubmissionPartial

This lightweight submission object is used to contain the information gathered when parsing gallery, scraps, favorites
and search pages. It contains only the following fields:

* `id: int` submission id
* `title: str` submission title
* `author: UserPartial` submission author (only the `name` field is filled)
* `rating: str` submission rating [general, mature, adult]
* `type: str` submission type [text, image, etc...]
* `thumbnail_url: str` the URL to the submission thumbnail
* `submission_figure: bs4.element.Tag` the figure tag used to parse the object fields

`SubmissionPartial` objects can be directly cast to a dict object or iterated through.

#### Init

`__init__(submission_figure: bs4.element.Tag)`

`SubmissionPartial` init needs a figure tag taken from a parsed page.

#### Methods

* `url -> str`<br>
  Property method that returns the Fur Affinity URL to the submission (`https://www.furaffinity.net/view/{id}`).
* `parse(submission_figure: bs4.element.Tag)`<br>
  Parses the stored submission figure tag for information. If `submission_figure` is passed, it overwrites the
  existing `submission_figure` value.

### Submission

The main class that parses and holds submission metadata.

* `id: int` submission id
* `title: str` submission title
* `author: UserPartial` submission author (only the `name`, `title`, and `user_icon_url` fields are filled)
* `date: datetime` upload date as a [`datetime` object](https://docs.python.org/3/library/datetime.html) (defaults to
  timestamp 0)
* `tags: List[str]` tags list
* `category: str` category
* `species: str` species
* `gender: str` gender
* `rating: str` rating
* `type: str` submission type (text, image, etc...)
* `description: str` description in HTML format
* `mentions: List[str]` the users mentioned in the description (if they were mentioned as links, e.g. `:iconusername:`,
  `@username`, etc.)
* `folder: str` the submission folder (gallery or scraps)
* `file_url: str` the URL to the submission file
* `thumbnail_url: str` the URL to the submission thumbnail
* `submission_page: bs4.BeautifulSoup` the submission page used to parse the object fields
* `prev: int` the ID of the previous submission (if any)
* `next: int` the ID of the next submission (if any)

`Submission` objects can be directly cast to a dict object and iterated through.

#### Init

`__init__(submission_page: bs4.BeautifulSoup = None)`

To initialise the object, an optional `bs4.BeautifulSoup` object is needed containing the parsed HTML of a submission
page.

If no `submission_page` is passed then the object fields will remain at their default - empty - value.

#### Methods

* `url -> str`<br>
  Property method that returns the Fur Affinity URL to the submission (`https://www.furaffinity.net/view/{id}`).
* `parse(submission_page: bs4.BeautifulSoup = None)`<br>
  Parses the stored submission page for metadata. If `submission_page` is passed, it overwrites the
  existing `submission_page` value.

### UserPartial

A stripped-down class that holds basic user information. It is used to hold metadata gathered when parsing a submission,
journal, gallery, scraps, etc.

* `name: str` display name with capital letters and extra characters such as "_"
* `status: str` user status (~, !, etc.)
* `title: str` the user title as it appears on their userpage
* `join_date: datetime` the date the user joined (defaults to timestamp 0)
* `user_tag: bs4.element.Tag` the user element used to parse information (placeholder, `UserPartial` is filled
  externally)

#### Init

`__init__(user_tag: bs4.element.Tag = None)`

To initialise the object, an optional `bs4.element.Tag` object is needed containing the user element from a user page or
user folder.

If no `user_tag` is passed then the object fields will remain at their default - empty - value.

#### Methods

* `name_url -> str`<br>
  Property method that returns the URL-safe username
* `url -> str`<br>
  Property method that returns the Fur Affinity URL to the user (`https://www.furaffinity.net/user/{name_url}`).
* `parse(user_page: bs4.BeautifulSoup = None)`<br>
  Parses the stored user page for metadata. If `user_page` is passed, it overwrites the existing `user_page` value.

### User

A class that holds a user's main information.

* `name: str` display name with capital letters and extra characters such as "_"
* `status: str` user status (~, !, etc.)
* `title: str` the user title as it appears on their userpage
* `join_date: datetime` the date the user joined (defaults to timestamp 0)
* `profile: str` profile text in HTML format
* `stats: UserStats` user statistics sorted in a `namedtuple` (`views`, `submissions`, `favs`, `comments_earned`
  , `comments_made`, `journals`, `watched_by`, `watching`)
* `info: Dict[str, str]` profile information (e.g. "Accepting Trades", "Accepting Commissions", "Character Species",
  etc.)
* `contacts: Dict[str, str]` contact links (e.g. Twitter, Steam, etc.)
* `user_icon_url: str` the URL to the user icon
* `user_page: bs4.BeautifulSoup` the user page used to parse the object fields

#### Init

`__init__(user_page: bs4.BeautifulSoup = None)`

To initialise the object, an optional `bs4.BeautifulSoup` object is needed containing the parsed HTML of a submission
page.

If no `user_page` is passed then the object fields will remain at their default - empty - value.

#### Methods

* `name_url -> str`<br>
  Property method that returns the URL-safe username
* `url -> str`<br>
  Property method that returns the Fur Affinity URL to the user (`https://www.furaffinity.net/user/{name_url}`).
* `parse(user_page: bs4.BeautifulSoup = None)`<br>
  Parses the stored user page for metadata. If `user_page` is passed, it overwrites the existing `user_page` value.

## Contributing

All contributions and suggestions are welcome!

The only requirement is that any merge request must be sent to the GitLab project as the one on GitHub is only a
mirror: [GitLab/FALocalRepo](https://gitlab.com/MatteoCampinoti94/FALocalRepo)

If you have suggestions for fixes or improvements, you can open an issue with your idea, see [#Issues](#issues) for
details.

## Issues

If any problem is encountered during usage of the program, an issue can be opened on the project's pages
on [GitLab](https://gitlab.com/MatteoCampinoti94/FAAPI/issues) (preferred)
or [GitHub](https://github.com/MatteoCampinoti94/FAAPI/issues) (mirror repository).

Issues can also be used to suggest improvements and features.

When opening an issue for a problem, please copy the error message and describe the operation in progress when the error
occurred.
