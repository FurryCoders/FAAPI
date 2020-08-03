from json import dumps
from os import path
from sys import argv
from typing import List

import faapi

if __name__ == "__main__":
    work_dir: str = path.dirname(path.abspath(__file__))

    # Prepare cookies
    #  Populate values using 1st and 2nd argument
    cookies: List[dict] = [
        {"name": "a", "value": argv[1]},
        {"name": "b", "value": argv[2]},
    ]

    # Initialise the API with the cookies
    api: faapi.FAAPI = faapi.FAAPI(cookies)

    gallery: List[faapi.SubPartial] = []
    gallery_page: List[faapi.SubPartial] = []
    page: int = 1

    # Download all the pages of a user's gallery until the last one is reached.
    #  Use 3rd argument as user
    while page > 0:
        print("Downloading page", page)
        gallery_page, page = api.gallery(argv[3], page)
        gallery.extend(gallery_page)

    # Save downloaded submissions into a json file
    with open(path.join(work_dir, f"{argv[3]}-gallery.json"), "w") as f:
        f.write(dumps(list(map(dict, gallery)), indent=2))
