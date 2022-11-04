# Changelog

## v3.9.5

### Changes

* Improve parsing of usernames and statuses
    * Thanks to PR [#7](https://github.com/FurryCoders/FAAPI/pull/7) by @Xraydylan

### Fixes

* Fix parsing of user tags for folders when the user had no title set, or used bars (`|`) in their title

## v3.9.4

### Fixes

* Fix admins' username and status not being parsed correctly in watchlists and users tags
    * Fix issue [#6](https://github.com/FurryCoders/FAAPI/issues/6)

## v3.9.3

### Changes

* Users with non-alphanumeric characters in their name are now escaped in URLs
    * From suggestion in issue [#5](https://github.com/FurryCoders/FAAPI/issues/5)

### Fixes

* Fix admins' username and status not being parsed correctly
    * Fix issue [#6](https://github.com/FurryCoders/FAAPI/issues/6)

## v3.9.2

### Fixes

* Fix ` being removed from usernames

## v3.9.1

### Fixes

* Fix incorrect user icon URLs when converting BBCode to HTML

### Dependencies

* Use [pytest ^7.2.0](https://pypi.org/project/pytest/7.2.0)
    * Fix [CVE-2022-42969](https://cve.report/CVE-2022-42969.pdf) issue

## v3.9.0

### New Features

* Submission footers
    * Submission footers are now separated from the submission description and stored in the `Submission.footer` field
    * The BBCode of the footer can be accessed with the `Submission.footer_bbcode` property
* Generate user icon URLs
    * New `generate_user_icon_url()` method added to `UserPartial` and `User` to create the URL for the current user
      icon
* BBCode to HTML conversion
    * Work-in-progress version of a BBCode converter based on the [bbcode](https://pypi.org/project/bbcode) library
    * Converter function is located in the `parse` submodule: `faapi.parse.bbcode_to_html()`
    * The majority of HTML fields (submission descriptions, journal contents, comments, etc.) can be converted back and
      forth between HTML and BBCode without loosing information
    * If a submission contains incorrect or very unusual BBCode tags or text, the BBCode to HTML conversion may create
      artifacts and tags that did not exist in the original content

### Changes

* Added `Journal.header_bbcode` and `Journal.footer_bbcode` properties to convert `Journal.header` and `Journal.footer`
  to BBCode
* Return `None` instead of 0 (or `""` for favorites) when reaching the last page with `FAAPI.gallery()`
  , `FAAPI.scraps()`, `FAAPI.journals()`, `FAAPI.favorites()`, `FAAPI.watchlist_by()`, and `FAAPI.watchlist_to()`
* Added `__hash__` method to `User`, `UserPartial`, `Submission`, `SubmissionPartial`, `Journal`, `JournalPartial`,
  and `Comment`; the hash value is calculated using the same fields used for equality comparisons
* Improved cleanup of HTML fields by using [htmlmin](https://pypi.org/project/htmlmin)
* Fur Affinity URLs are now properly converted to relative `[url=<path>]` tags in BBCode
* Unknown tags are converted to `[tag=<name>.<classes>]` in BBCode
* Added `CookieDict(TypedDict)` notation for cookies dictionary (alternative to `CookieJar`) to provide intellisense and
  type checking information

### Fixes

* Fix comments being considered equal even if they had different parents but the same ID
* Fix break lines tags (`<br/>`) not always being converted to newlines when converting to BBCode
* Fix errors when converting nav links (e.g. `[2,1,3]`) to BBCode
* Fix incorrect detection of last page in `FAAPI.watchlist_by()` and `FAAPI.watchlist_by()`
* Fix errors when converting special characters (e.g. `&`)
* Fix trailing spaces around newlines remaining after converting to BBCode
* Fix horizontal lines not being correctly converted from BBCode if the dashes (`-----` or longer) were not surrounded
  by newlines

### Dependencies

* Added [htmlmin ^0.1.12](https://pypi.org/project/htmlmin/0.1.12)
* Added [bbcode ^1.1.0](https://pypi.org/project/bbcode/1.1.0)

## v3.8.1

### Changes

* Improved HTML extraction for specific tags to avoid encoding issues
* HTML fields are cleaned up (i.e., removed newlines, carriage returns, and extra spaces)
    * None of the parsed pages use tags with _pre_ white space rendering, so no information is lost
* Improvements to BBCode conversion
    * Do not quote URLs when converting to BBCode
    * Support nested quote blocks
    * Support non-specific tags (e.g. `div.submission-footer`) and convert them
      to `[tag.<tag name>.<tag class>][/tag.<tag.name>]`

### Fixes

* Fix incorrect encoding of special characters (`<`, `>`, etc.) in HTML fields
    * Was caused by the previous method of extracting the inner HTML of a tag
* Fix URLs automatically shortened by Fur Affinity being converted to BBCode with the wrong text content
* Fix HTML paragraph tags (`<p>`) sometimes appearing in BBCode-converted content
* Fix BBCode conversion of `:usernameicon:` links (i.e., user icon links without the username)

## v3.8.0

### New Features

* Submission user folders
    * Submission folders are now parsed and stored in a dedicated `user_folders` field in the `Submission` object
    * Each folder is stored in a `namedtuple` with fields for `name`, `url`, and `group` (if any)
* BBCode conversion
    * New properties have been added to the `User`, `Submission`, `Journal`, `JournalPartial`, and `Comment` objects to
      provide BBCode versions of HTML fields
    * The generated BBCode tags follow the Fur Affinity standard found on
      their [support page](https://www.furaffinity.net/help/#tags-and-codes)

## v3.7.4

### Dependencies

* Use [lxml ^4.9.1](https://pypi.org/project/lxml/4.9.1)
    * Fix [CVE-2022-2309](https://cve.report/CVE-2022-2309.pdf) issue

## v3.7.3

### Fixes

* Fix error when parsing journals folders and journal pages caused by date format set to full on Fur Affinity's site
  settings

## v3.7.2

### New Features

* Requests timeout
    * New `FAAPI.timeout: int | None` variable to set request timeout in seconds
    * Timeout is used for both page requests (e.g. submissions) and file requests

### Fixes

* Fix possible parsing error arising from multiple attributes in one tag

## v3.7.1

### New Features

* Frontpage
    * New `FAAPI.frontpage()` method to get submissions from Fur Affinity's front page
* Sorting of `Journal`, `Submission`, and `User` objects
    * All data objects now support greater than, greater or equal, lower than, and lower or equal operations for easy
      sorting

### Fixes

* Fix equality comparison between `Journal` and `JournalPartial`
* Fix parsing of usernames from user pages returning the title instead
    * Caused by a change in Fur Affinity's DOM

## v3.7.0

### New Features

* Journal headers and footers
    * The `Journal` class now contains header and footer fields which are parsed from journal pages (`FAAPI.journal`)
* Submission favorite status and link
    * The `Submission` class now contains a boolean `favorite` field that is set to `True` if the submission is a
      favorite, and a `favorite_toggle_link` containing the link to toggle the favorite status (`/fav/` or `/unfav/`)
* User watch and block statuses and links
    * The `User` class now contains boolean `watched` and `blocked` fields that are set to `True` if the user is watched
      or blocked respectively, and `watched_toggle_link` and `blocked_toggle_link` fields containing the links to toggle
      the watched (`/watch/` or `/unwatch/`) and blocked (`/block/` or `/unblock/`) statuses respectively.

### Changes

* Remove `parse.check_page` function which had no usage in the library anymore
* Remove `parse.parse_search_submissions` function and `FAAPI.search` method
    * They will be reintroduced once Fur Affinity allows scraping search pages again

### Fixes

* Fix an incorrect regular expression that parsed mentions in journals, submissions, and profiles which could cause
  non-Fur Affinity links to be matched as valid
    * Security issue [#3](https://github.com/FurryCoders/FAAPI/issues/3)

## v3.6.1

### Fixes

* Fix `FAAPI.journals` not detecting the next page correctly
    * Caused by a change in Fur Affinity's journals page

## v3.6.0

### New Features

* Comments! 💬
    * A new `Comment` object is now used to store comments for submissions and journals
    * The comments are organised in a tree structure, and each one contains references to both its parent
      object (`Submission` or `Journal`) and, if the comment is a reply, to its parent comment too
    * The auxiliary functions `faapi.comment.flatten_comments` and `faapi.comment.sort_comments` allow to flatten the
      comment tree or reorganise it

* Separate `JournalPartial` and `Journal` objects
    * The new `JournalPartial` class takes the place of the previous `Journal` class, and it is now used only to parse
      journal from a user's journals folder
    * The new `Journal` class contains the same fields as `JournalPartial` with the addition of comments, and it is only
      used to parse journal pages

* Comparisons
    * All objects can now be used with the comparison (==) operator with other objects of the same type or the type of
      their key property (`id: int` for submissions and journals, and `name_url: str` for users)

### Changes

* The `cookies` argument of `FAAPI` is now mandatory, and an `Unauthorized` exception is raised if `FAAPI` is
  initialised with an empty cookies list
* The list of `Submission`/`Journal` objects returned by `FAAPI.gallery`, `FAAPI.scraps`, and `FAAPI.journals` now uses
  a shared `UserPartial` object in the `author` variable (i.e. changing a property of the author in one object of the
  list will change it for the others as well)

### Fixes

* Fix path checking against robots.txt not working correctly with paths missing a leading forward slash

## v3.5.0

### New Features

* New `Submission.stats` field for submission statistics stored in a named tuple (`views`, `comments` (count)
  , `favorites`)
    * Pull request [#2](https://github.com/FurryCoders/FAAPI/pull/2), thanks
      to [@warpKaiba](https://github.com/warpKaiba)!
* New `Journal.stats` field for journal statistics stored in a named tuple (`comments` (count))

### Changes

* Rename `UserStats.favs` to `UserStats.favorites`

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
* Error messages from server are not lowercase

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

