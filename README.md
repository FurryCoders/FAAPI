# Fur Affinity API

[![version_pypi](https://img.shields.io/pypi/v/faapi?logo=pypi)](https://pypi.org/project/faapi/)
[![version_gitlab](https://img.shields.io/badge/dynamic/json?logo=gitlab&color=orange&label=gitlab&query=%24%5B%3A1%5D.name&url=https%3A%2F%2Fgitlab.com%2Fapi%2Fv4%2Fprojects%2Fmatteocampinoti94%252Ffaapi%2Frepository%2Ftags)](https://gitlab.com/MatteoCampinoti94/FAAPI)
[![version_python](https://img.shields.io/pypi/pyversions/faapi?logo=Python)](https://www.python.org)

[![issues_gitlab](https://img.shields.io/badge/dynamic/json?logo=gitlab&color=orange&label=issues&suffix=%20open&query=%24.length&url=https%3A%2F%2Fgitlab.com%2Fapi%2Fv4%2Fprojects%2Fmatteocampinoti94%252Ffaapi%2Fissues%3Fstate%3Dopened)](https://gitlab.com/MatteoCampinoti94/FAAPI/issues)
[![issues_github](https://img.shields.io/github/issues/matteocampinoti94/faapi?logo=github&color=blue)](https://github.com/MatteoCampinoti94/FAAPI/issues)

Python module to implement API-like functionality for the FurAffinity.net website

## Requirements

Python 3.8+ is necessary to run this module.

This module requires the following pypi modules:

* [beautifulsoup4](https://www.crummy.com/software/BeautifulSoup/)
* [cfscrape](https://github.com/Anorov/cloudflare-scrape)
* [lxml](https://github.com/lxml/lxml/)
* [requests](https://github.com/requests/requests)
* [python-dateutil](https://github.com/dateutil/dateutil/)

## Usage

The API is comprised of a main class `FAAPI` and two submission classes: `Submission` and `SubmissionPartial`.
Once `FAAPI` is initialized its method can be used to crawl FA and return machine-readable objects.

```python
import faapi
import json

cookies = [
    {"name": "a", "value": "38565475-3421-3f21-7f63-3d341339737"},
    {"name": "b", "value": "356f5962-5a60-0922-1c11-65003b703038"},
]

api = faapi.FAAPI(cookies)
sub, sub_file = api.get_submission(12345678,get_file=True)

print(sub.id, sub.title, sub.author, f"{len(sub_file)/1024:02f}KiB")

with open(f"{sub.id}.json", "w") as f:
    f.write(json.dumps(sub))

with open(sub.file_url.split("/")[-1], "wb") as f:
    f.write(sub_file)

gallery, _ = api.gallery("user_name", 1)
with open("user_name-gallery.json", "w") as f:
    f.write(json.dumps(gallery))
```

### robots.txt

At init, the `FAAPI` object downloads the [robots.txt](https://www.furaffinity.net/robots.txt) file from FA to determine the `Crawl-delay` value set therein. If not set, a value of 1 second is used.

To respect this value, the default behaviour of of the `FAAPI` object is to wait when a get request is made if the last request was performed more recently then the crawl delay value.

See under [FAAPI](#faapi) for more details on this behaviour.

Furthermore, any get operation that points to a disallowed path from robots.txt will raise an exception. This check should not be circumvented and the developer of this module does not take responsibility for violations of the TOS of Fur Affinity.

### Cookies

To access protected pages, cookies from an active session are needed. These cookies must be given to the FAAPI object as a list of dictionaries, each containing a `name` and a `value` field. The cookies list should look like the following random example:

```python
cookies = [
    {"name": "a", "value": "38565475-3421-3f21-7f63-3d341339737"},
    {"name": "b", "value": "356f5962-5a60-0922-1c11-65003b703038"},
]
```

Only cookies `a` and `b` are needed.

To access session cookies, consult the manual of the browser used to login.

*Note:* it is important to not logout of the session the cookies belong to, otherwise they will no longer work.

## FAAPI

This is the main object that handles all the calls to scrape pages and get submissions.

It holds 6 different fields:

* `cookies: List[dict] = []` cookies passed at init
* `session: CloudflareScraper` cfscrape session used for get requests
* `robots: Dict[str, List[str]]` robots.txt values
* `crawl_delay: float` crawl delay from robots.txt, else 1
* `last_get: float` time of last get (not UNIX time, uses `time.perf_counter` for more precision)
* `raise_for_delay: bool = False` if set to `True`, raises an exception if a get call is made before enough time has passed

### Init

`__init__(cookies: List[dict] = None)`

The class init has a single optional argument `cookies` necessary to read logged-in-only pages.
The cookies can be omitted and the API will still be able to access public pages.

*Note:* Cookies must be in the format mentioned above in [#Cookies](#cookies).

### Methods & Properties

* `load_cookies(cookies: List[Dict[str, Any]])`<br>
Load new cookies in the object and remake the `CloudflareScraper` session.
* `connection_status -> bool`<br>
Returns the status of the connection.
* `get(path: str, **params) -> requests.Response`<br>
This returns a response object containing the result of the get operation on the given url with the optional `**params` added to it (url provided is considered as path from 'https://www.furaffinity.net/').
* `get_parse(path: str, **params) -> bs4.BeautifulSoup`<br>
Similar to `get()` but returns the parsed  HTML from the normal get operation.
* `get_submission(submission_id: int, get_file: bool = False) -> Tuple[Submission, Optional[bytes]]`<br>
Given a submission ID, it returns a `Submission` object containing the various metadata of the submission itself and a `bytes` object with the submission file if `get_file` is passed as `True`.
* `get_submission_file(submission: Submission) -> Optional[bytes]`<br>
Given a submission object, it downloads its file and returns it as a `bytes` object.
* `userpage(user: str) -> Tuple[str, str, bs4.BeautifulSoup]`<br>
Returns the user's full display name - i.e. with capital letters and extra characters such as "_" -, the user's status - the first character found beside the user name - and the parsed profile text as a parsed object.
* `gallery(user: str, page: int = 1) -> Tuple[List[SubmissionPartial], int]`<br>
Returns the list of submissions found on a specific gallery page and the number of the next page. The returned page number is set to 0 if it is the last page.
* `scraps(user: str, page: int = 1) -> -> Tuple[List[SubmissionPartial], int]`<br>
Returns the list of submissions found on a specific scraps page and the number of the next page. The returned page number is set to 0 if it is the last page.
* `favorites(user: str, page: str = "") -> Tuple[List[SubmissionPartial], str]`<br>
Downloads a user's favorites page. Because of how favorites pages work on FA, the `page` argument (and the one returned) are strings. If the favorites page is the last then an empty string is returned as next page. An empty page value as argument is equivalent to page 1.<br>
*Note:* favorites page "numbers" do not follow any scheme and are only generated server-side.
* `journals(user: str, page: int = 1) -> -> Tuple[List[Journal], int]`<br>
Returns the list of submissions found on a specific journals page and the number of the next page. The returned page number is set to 0 if it is the last page.
* `search(q: str = "", page: int = 0, **params) -> Tuple[List[SubmissionPartial], int, int, int, int]`<br>
Parses FA search given the query (and optional other params) and returns the submissions found and the next page together with basic search statistics: the number of the first submission in the page (0-indexed), the number of the last submission in the page (0-indexed), and the total number of submissions found in the search. For example if the the last three returned integers are 0, 47 and 437, then the the page contains submissions 1 through 48 of a search that has found a total of 437 submissions.<br>
*Note:* as of October 2020 the "/search" path is disallowed by Fur Affinity's robots.txt.
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


## Journal

This object contains information gathered when parsing a journals page or a specific journal page. It contains the following fields:

* `id` journal id
* `title` journal title
* `date` upload date in YYYY-MM-DD format
* `author` journal author
* `content` journal content

`Journal` objects can be directly casted to a dict object or iterated through.

### Init

`__init__(journal_item: Union[bs4.element.Tag, bs4.BeautifulSoup] = None)`

`Journal` takes one optional parameters: a journal section tag from a journals page or a parsed journal page. Parsing is then performed based on the class of the passed object.

The tag/page is saved as an instance variable of the same name

### Methods

* `parse()`<br>
Parses the stored journal tag/page for information.

## SubmissionPartial

This lightweight submission object is used to contain the information gathered when parsing gallery, scraps, favorites and search pages. It contains only the following fields:

* `id` submission id
* `title` submission title
* `author` submission author
* `rating` submission rating [general, mature, adult]
* `type` submission type [text, image, etc...]

`SubmissionPartial` objects can be directly casted to a dict object or iterated through.

### Init

`__init__(submission_figure: bs4.element.Tag)`

`SubmissionPartial` init needs a figure tag taken from a parsed page. The tag is saved as an instance variable of the same name.

### Methods

* `parse()`<br>
Parses the stored submission figure tag for information.

## Submission

The main class that parses and holds submission metadata.

* `id` submission id
* `title` submission title
* `author` submission author
* `date` upload date in YYYY-MM-DD format
* `tags` tags list
* `category` category \*
* `species` species \*
* `gender` gender \*
* `rating` rating \*
* `description` the description as an HTML formatted string
* `file_url` the url to the submission file

\* these are extracted exactly as they appear on the submission page

`Submission` objects can be directly casted to a dict object and iterated through.

### Init

`__init__(submission_page: bs4.BeautifulSoup = None)`

To initialise the object, An optional `bs4.BeautifulSoup` object is needed containing the parsed HTML of a submission page.

The `submission_page` argument is saved as an instance variable and is then parsed to obtain the other fields.

If no `submission_page` is passed then the object fields will remain at their default - empty - value.

### Methods

* `parse()`<br>
Parses the stored submission page for metadata.

## Contributing

Al contributions and suggestions are welcome!

The only requirement is that any merge request must be sent to the GitLab project as the one on GitHub is only a mirror: [GitLab/FALocalRepo](https://gitlab.com/MatteoCampinoti94/FALocalRepo)

If you have suggestions for fixes or improvements, you can open an issue with your idea, see [#Issues](#issues) for details.

## Issues

If any problem is encountered during usage of the program, an issue can be opened on the project's pages on [GitLab](https://gitlab.com/MatteoCampinoti94/FAAPI/issues) (preferred) or [GitHub](https://github.com/MatteoCampinoti94/FAAPI/issues) (mirror repository).

Issues can also be used to suggest improvements and features.

When opening an issue for a problem, please copy the error message and describe the operation in progress when the error occurred.
