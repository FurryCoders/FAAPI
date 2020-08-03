from sys import argv
from typing import List

import faapi

if __name__ == '__main__':
    # Prepare cookies
    #  Populate values using 1st and 2nd argument
    cookies: List[dict] = [
        {"name": "a", "value": argv[1]},
        {"name": "b", "value": argv[2]},
    ]

    # Initialise the API with the cookies
    api: faapi.FAAPI = faapi.FAAPI(cookies)

    sub: faapi.Sub
    sub_file: bytes

    # Get submission metadata without downloading file
    #  Use 3rd argument as ID
    sub, _ = api.get_sub(argv[3])

    # Access submission metadata
    print(f"id         : {sub.id}")
    print(f"title      : {sub.title}")
    print(f"author     : {sub.author}")
    print(f"date       : {sub.date}")
    print(f"tags       : {sub.tags}")
    print(f"category   : {sub.category}")
    print(f"spec       : {sub.species}")
    print(f"gender     : {sub.gender}")
    print(f"rating     : {sub.rating}")
    print(f"description: {sub.description[:100]}")
    print(f"file       : {sub.file_url}")

    # Download submission file in a separate step
    sub_file = api.get_sub_file(sub)

    # Write submission file to file
    with open(sub.file_url.split('/')[-1], "wb") as f:
        f.write(sub_file)
