# Changelog

## v3.5.0

### New Features

* New `Submission.stats` field for submission statistics stored in a named tuple (`views`, `comments` (count)
  , `favorites`)
    * Pull request [#2](https://github.com/FurryCoders/FAAPI/pull/2), thanks
      to [@warpKaiba](https://github.com/warpKaiba)!
* New `Journal.stats` field for journal statistics stored in a named tuple (`comments` (count))

### Fixes

* Fix links in PyPi metadata pointing to previous hosting at GitLab

## v3.4.3

### Changes

* Better and more resilient robots.txt parsing

### Fixes

* Fix spaces around slash (/) not being preserved for submission categories

## v3.4.2

### Changes

* Raise `DisabledAccount` for users pending deletion
* Error messages from server are not lowercased

## v3.4.1

### Fixes

* Fix rare occurrence of error message not being parsed if inside a `section.notice-message`

## v3.4.0 (was 3.3.8)

### New Features

* New `NotFound` exception inheriting from `ParsingError`

### Changes

* Removed `FAAPI.submission_exists`, `FAAPI.journal_exists`, and `FAAPI.user_exists` methods
* Improved reliability of error pages' parser

### Fixes

* Custom exceptions inherit from `Exception` instead of `BaseException`

## v3.3.7

### Changes

* No changes to code; migrated repository to GitHub and updated README and PyPi metadata

## v3.3.6

### Changes

* Allow empty info/contacts when parsing user profiles

## v3.3.5

### Changes

* Fix last page check when parsing galleries

## v3.3.4

### Changes

* Use BaseException as base class of custom exceptions

### Dependencies

* Use [requests ^2.27.1](https://pypi.org/project/requests/2.27.1)

## v3.3.3

### Changes

* Allow submission thumbnail tag to be null

## v3.3.2

### Changes

* Use `UserStats` class to hold user statistics instead of namedtuple
* Add watched by and watching stats to `UserStats`

## v3.3.1

### Changes

* Safer parsing

## v3.3.0

### New Features

* Add docstrings
* Handle robots.txt parsing with `urllib.RobotFileParser`
* `User-Agent` header is exposed as `FAAPI.user_agent` property

### Changes

* `FAAPI.last_get` uses UNIX time
* `FAAPI.check_path` doesn't raise an exception by default
* `FAAPI.login_status` does not raise an exception on unauthorized
* Remove crawl delay error
* Improve download of files

## v3.2.0

### New Features

* `FAAPI.get_parsed` checks login status and checks the page for errors directly (both can be manually skipped)
* Add `Unauthorized` exception

## v3.1.2

### New Features

* `FAAPI.submission` and `FAAPI.submission_file` support setting the chunk size for the binary file download

### Changes

* The file downloader uses chunk size instead of speed

## v3.1.1

### Changes

* When raising `ServerError` and `NoticeMessage`, the actual messages appearing on the page are use as exception
  arguments

## v3.1.0

### New feature

* Add support for `http.cookiejar.CookieJar` (and inheriting classes, like `requests.cookies.RequestsCookieJar`) for
  cookies.
* Add `FAAPI.me()` method to get the logged-in user
* Add `FAAPI.login_status` property to get the current login status

### Dependencies

* Use [lxml ^4.7.1](https://pypi.org/project/lxml/4.7.1)
    * Fix [CVE-2021-43818](https://cve.report/CVE-2021-43818.pdf) issue

## v3.0.2

### Fixes

* Fix rare error when parsing the info section of a userpage

## v3.0.1

### Fixes

* Fix a key error in `Submission` when assigning the parsed results

## v3.0.0

### New Features

* Upgrade to Python 3.9+
    * Update type annotations
* `Submission` parses next and previous submission IDs
* `FAAPI.watchlist_by()` and `FAAPI.watchlist_to()` methods support multiple watchlist pages

### Changes

* Renamed `FAAPI.get_parse` to `get_parsed`
* Removed _get_ prefix from `FAAPI` methods (e.g. `get_submission` to `submission`) and return a list of `UserPartials`
  objects instead of `Users`
* Added `__all__` declarations to allow importing exceptions and secondary functions from `connection` and `parse`
* `datetime` fields are not serialised on `__iter__` (e.g. when casting a `Submission` object to `dict`)

