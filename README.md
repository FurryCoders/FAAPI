# FAAPI

Python module to implement API-like functionality for the FurAffinity.net website

## Requirements
This module requires the following pypi modules:<br>
* [beautifulsoup4](https://www.crummy.com/software/BeautifulSoup/)
* [cfscrape](https://github.com/Anorov/cloudflare-scrape)
* [lxml](https://github.com/lxml/lxml/)
* [requests](https://github.com/requests/requests)

---

## Usage
The api is comprised of a main class `FAAPI` and a submission handling class, `FASub`. Once `FAAPI` is initialized its method can be used to access FA and return machine-readable objects.

See `Classes`&rarr;`FAAPI` for details on the user-facing methods available.

See `Classes`&rarr;`FASub` for details on the submission object.

---

## Classes
### FAAPI
This is the main class of the api and its methods are the ones that provided the easiest way to access the various functions and methods provided by the other sections of the module.

It is suggested to only use this class' methods as the ones provided by the other classes require special variables that `FAAPI` handles directly without the need to implement any special code.

#### init
`FAAPI` supports 5 optional arguments:<br>
* `cookies_f` - the name of the file containing the cookies necessary for the api to operate.
* `cookies_l` - a json formatted (list of dicts) list containing the cookies necessary for the api to operate.
* `logger_norm` - a function that logs `FAAPI` main operations, defaults to a `None` lambda function.
* `logger_verb` - a function that logs the operations of the various subclasses, defaults to a `None` lambda function.
* `logger_warn` - a function that logs warnings and errors, defaults to a `None` lambda function.

When `FAAPI` is initialized it does 4 things:
1. saves the logger functions (if present).

2. initializes the `FASession` class with the cookies variables and the verbose logger. It creates a `cfscrape.CloudflareScraper` object (it's similar to `requests.Session`, supports the same methods) (this object is going to be referred as `Session` in the rest of the documentation). If no cookies are provided then the `Session` object is declared `None`.<br>
The `FAsession` object is saved as instance variable `FAAPI.Session`.<br>
(See `FASession` for more details)

3. initializes the `FAGet` class with the `Session` created earlier and verbose logger.

4. initializes the `FAPage` class with the verbose logger


The needed objects are saved as instanced variables:<br>
* `FAAPI.Session` = `FASession()`
* `FAAPI.Get` = `FAGet()`
* `FAAPI.Page` = `FAPage()`


#### Methods
1. `get(url, **params)`<br>
This returns a `requests.models.Response` object containing the result of the get operation on the given url (url provided is added to 'https://www.furaffinity.net/') with the optional `**params` added.

2. `getParse(url, **params)`<br>
Similar to `get()` but returns a `bs4.BeautifulSoup` object with the parsed html from the normal get operation.

3. `getSub(ID, file=False)`<br>
Given a submission ID in either int or str format, it returns an `FASub` object containing the various metadata of the submission itself and a `bytes` variable with its file (see `FASub` for details). The `FASub` object is initialized with a function that can download it's file. If the optional `file` argument is passed as `True` then the file is downloaded automatically, otherwise the returned object contains an empty `bytes` variable and the file can be downloaded using the `FASub.getFile()` method.

4. `userpage(user)`<br>
The provided user's main page is downloaded and returned as a `bs4.BeautifulSoup` object.

5. `gallery(user, page=1)`<br>
Returns the list of submissions tags from the provided user's gallery as `bs4.BeautifulSoup` objects and the number of the next page in a two elements list (`[tags, next page]`). By default it returns the first page of the gallery but the optional `page` argument can be set to get any specific page.

6. `scraps(user, page=1)`<br>
Same as `gallery()`  but gets a user's scraps page instead.

7. `favorites(user, page='')`<br>
As `gallery()` and `scraps()` it downloads a user's favorites page. Because of how favorites pages work on FA, the `page` argument (and the one returned) are URLs, if the favorites page is the last then an empty string is returned as next page.

8. `search(q='', **params)`<br>
Searches the website and returns the submissions found. The `q` argument cannot be empty. `**params` can be used to specify the page. The next page is returned as a dict object `{'page': n}` which can be expanded when calling search again, if there is no next page an empty string is returned instead.


### FASession
This class provides the method that creates and tests the Session object and the provided cookies. It is also used to store the cookies and the Session variable itself.

#### init
`FASession` supports 4 optional arguments:<br>
* `cookies_f` - the name of the file containing the cookies necessary for the api to operate.
* `cookies_l` - a json formatted (list of dicts) list containing the cookies necessary for the api to operate.
* `logger` - a function that logs the operations of the class, defaults to a `None` lambda function.
* `logger_warn` - a function that logs warnings and errors, defaults to a `None` lambda function.

When `FASession` is initialized it saves the cookies arguments as instanced variables and creates a `None` Session variable as placeholder.

The second step in the init is launching the `FASession.makeSession()` method as detailed below.

#### Methods
1. `makeSession()`:
This method is responsible for creating the `cfscrape.CloudflareScraper` object (Session) used by the api's get methods.<br>
It is divided in different steps:<br>
    1. pings 'http://www.furaffinity.net' using the `FASession.ping()` method to ensure that there is a stable connection available.<br>
    If a connection cannot be established `makeSession` is interrupted.

    2. if the `cookies_l` argument is empty then it opens the file passed by `cookies_f` using `json.load()` to extract its contents.<br>
    if `cookies_l` is provided then `cookies_f` is ignored.<br>
    If `cookies_l` is empty and the file is missing, not provided or contains errors then `makeSession` is interrupted.

    3. the cookies extracted from `cookies_f` or the ones provided with `cookies_l` are parsed to isolate only the 'name' and 'value' fields as those are the only ones required by the Session object.

    4. the Session variable is created as a `cfscrape.CloudflareScraper` object and the cookies are loaded into it with the `Session.cookies.set()` method.

    5. an `FAGet` object is temporarily initialized with the just created session and the loggers and its `getParse()` method is used to get the '/controls/settings/' page from FA as its content changes depending on whether a user is logged in or not.

    6. an `FAPage` object is temporarily created to get the `<a id="my-username">` tag from the parsed page that was downloaded in the previous step.<br>
    if the parser cannot find the tag then the cookies are not valid and the Session object is reset to `None`. If the tag is found then the init is complete.

2. `ping(url)`<br>
Simple method that uses a `requests.Session` object to check the connection to the provided url.


### FAGet
This class handles all GET requests. Requests and binary downloads are throttled automatically to 1 request every 12 seconds (5 requests per minute) and a download speed of maximum 100KiB/s for binary data. These values cannot be overridden in any way: the module only exports the `FAAPI` class and an instance of the `FAGet` class. Since these values are saved as class variables they cannot be changed from outside the module itself.

#### init
The init for this class simply saves the the provided Session object and the loggers. It also creates an instanced variable which contains the time of the last get operation and defaults to `-interval` (with interval being the minimum time between requests) as a safety measure in case the time is set to 0 so that the get request can be made immediately.

All get requests are made using the base url 'https://www.furaffinity.net/'

#### Methods
1. `get(url, **params)`<br>
Return `requests.models.Response` object from the given url with the passed `**params` added to it.

2. `getParse(url, **params)`<br>
Uses `FAGet.get()` to download the url and then uses BeautifulSoup4 to parse it and return the parsed `bs4.BeautifulSoup` object.

3. `getBinary(url)`<br>
Downloads binary data (files) from given url.


### FAPage
This class simply provides logged methods to find tags in parsed `bs4.BeautifulSoup` objects.

#### init
The init simply stores the provided logger function into an instanced variable.

### Methods
1. `pageFind(page, **kwargs)`<br>
Returns the first tag that matches `**kwargs`. If no match can be found returns an empty list.

2. `pageFindAll(page, **kwargs)`<br>
Same as `FAPage.pageFind()` but returns all matches insteacd of only the first.


### FASub
This is the only other class exported by the module. It can take a submission `bs4.BeautifulSoup` object as argument and parse it saving the submission metadata as instance variables.

The `FASub` object can be directly converted to a dict object or iterated through.

#### init
`FASub` takes three arguments:<br>
* `sub` - the parsed html of the submission page, a `bs4.BeautifulSoup` object.
* `getBinary` - optional argument, a function that takes a URL as argument and returns a `bytes()` object.
* `logger` - optional argument, a logger for the class' methods

The sub argument is saved as an instance variable together with the getBinary and logger functions. An empty `bytes()` object is also declared for the submission file.

Once the variables are declared the `FASub.analyze()` method is called and the sub file is analyzed to extract the metadata.

#### Methods
1. `analyze()`<br>
The object's sub variable created during init is parsed using `bs4.BeautifulSoup` methods to find the relevant tags which are then processed to extract the metadata. Metadata can be called using the relevant instance variable (e.g. to get a downloaded submission author one would use `submisison.author` where `submission` is an`FASub` object)
The metadata variables are the following:<br>
    * `id` - the submission id
    * `title` - submission title
    * `author` - submission author
    * `date` - upload date in YYYY-MM-DD format
    * `keyw` - keywords list, sorted alphabetically
    * `category` - category \*
    * `species` - species \*
    * `gender` - gender \*
    * `rating` - rating \*
    * `desc` - the description as an html formatted string
    * `filelink` - the link to the submission file

    \* these are extracted exactly as they appear on the submission page

2. `getFile(getBinary=None)`<br>
This method can be called to download the submission file using the getBinary function saved at init or the one used as optional argument for the method. If the latter is present then it overrides the one saved at init.<br>
The getBinary function needs to take a url as argument and return a `bytes()` object, these are the only requirements but it is suggested to use the functioned included with the api at `FAAPI.Get.getBinary`.

---

## Examples
What follows are some examples of how to sue the api correctly.

The ID's and usernames used are random.

```Python
from faapi import *


# Create the api object without logger functions
#  using a file to load the cookies
api = FAAPI(cookies_f='cookies.json')


# Download a user's main page
user = api.userpage('abcdeABCDE1234')


# Download all of a user's favorites
#  the while cycle continues until the function
#  returns an empty next page value
next = '/'
favs = []
while next:
    favs += [api.favorites('abcdeABCDE5678', page=next)]
    next =  favs[-1][1]


# Download a search page
#  Search for 'forest tiger' using 'order-by=date' parameter
#  (need expanded dict since 'order-by' throws an error)
#  and select page 3
search = api.search(q='forest tiger', **{'order-by':'date'}, page=3)


# Download a submission
sub1 = api.getSub(ID=17042208)

# Print the various fields parsed by the submission
print(f'id  : {sub.id}')
print(f'titl: {sub.title}')
print(f'auth: {sub.author}')
print(f'date: {sub.date}')
print(f'keyw: {sub.keyw}')
print(f'catg: {sub.category}')
print(f'spec: {sub.species}')
print(f'gend: {sub.gender}')
print(f'ratn: {sub.rating}')
print(f'desc: {sub.desc}')
print(f'link: {sub.filelink}')

# Download the file for a submission
sub1.getFile()


# Download a submission and its file
sub2 = api.getSub(ID=17042213, file=True)


# Download a submission page as a parsed object
sub3 = api.getParse('/view/17042208')

# Create an FASub object manually
#  use the getBinary function provided by FAGet
sub3 = FASub(sub3, getBinary=api.Get.getBinary)
```
