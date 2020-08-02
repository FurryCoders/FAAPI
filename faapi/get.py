import requests
import bs4
import time

import traceback, sys


class FAGet:
    base_url = "https://www.furaffinity.net/"

    def __init__(self, Session):
        self.Session = Session

        self.interval = 12
        self.lastget = -self.interval
        self.throttle = 100 * 1024

    def get(self, url, **params):
        url = f'{FAGet.base_url.strip("/")}/{url.strip("/")}/'

        t = self.interval - (time.time() - self.lastget)
        if t > 0:
            time.sleep(t)

        self.lastget = time.time()

        try:
            get = self.Session.get(url, params=params)

            return get if get.ok else None
        except:
            err = traceback.format_exception(*sys.exc_info())
            err = ["FAGet get -> error: " + e.strip().replace("\n", " =") for e in err]
            return None

    def getParse(self, url, **params):
        get = self.get(url, **params)
        get = bs4.BeautifulSoup(get.text, "lxml") if get else None

        return get

    def getBinary(self, url):
        try:
            file_stream = self.Session.get(url, stream=True)
            file_binary = bytes()

            if not file_stream.ok:
                file_stream.close()
                return file_binary

            for chunk in file_stream.iter_content(chunk_size=1024):
                file_binary += chunk
                time.sleep(1 / (self.throttle / 1024) if self.throttle else 0)

            return file_binary
        except:
            err = traceback.format_exception(*sys.exc_info())
            err = ["FAGet get -> error: " + e.strip().replace("\n", " =") for e in err]
            return bytes()
