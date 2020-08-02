# FAAPI

Python module to implement API-like functionality for the FurAffinity.net website

## Requirements

This module requires the following pypi modules:<br>
* [beautifulsoup4](https://www.crummy.com/software/BeautifulSoup/)
* [cfscrape](https://github.com/Anorov/cloudflare-scrape)
* [lxml](https://github.com/lxml/lxml/)
* [requests](https://github.com/requests/requests)

## Usage
The api is comprised of a main class `FAAPI` and two submission handling classes: `Sub` and `SubPartial`.
Once `FAAPI` is initialized its method can be used to access FA and return machine-readable objects.

See [`Classes`&rarr;`FAAPI`](#FAAPI) for details on the user-facing methods available.

See [`Classes`&rarr;`Sub`]() for details on the submission object.

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

### Sub
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
    * `tags` - tags list, sorted alphabetically
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

```python
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
sub1 = api.get_sub(sub_id=17042208)

# Print the various fields parsed by the submission
print(f'id  : {sub.id}')
print(f'titl: {sub.title}')
print(f'auth: {sub.author}')
print(f'date: {sub.date}')
print(f'tags: {sub.tags}')
print(f'catg: {sub.category}')
print(f'spec: {sub.species}')
print(f'gend: {sub.gender}')
print(f'ratn: {sub.rating}')
print(f'desc: {sub.desc}')
print(f'link: {sub.filelink}')

# Download the file for a submission
sub1.getFile()


# Download a submission and its file
sub2 = api.get_sub(sub_id=17042213, file=True)


# Download a submission page as a parsed object
sub3 = api.get_parse('/view/17042208')

# Create an FASub object manually
#  use the getBinary function provided by FAGet
sub3 = FASub(sub3, get_binary=api.Get.get_binary)
```
