import requests
import bs4
import time

import traceback, sys

class FAGet():
    base_url = 'https://www.furaffinity.net/'
    interval = 12

    def __init__(self, Session, logger=(lambda *x: None)):
        logger('FAGet -> init')
        self.Session = Session
        self.lastget = -FAGet.interval
        self.Log     = logger

    def get(self, url, **params):
        self.Log(f'FAGet get -> url:{url} params:{params}')
        url = f'{FAGet.base_url.strip("/")}/{url.strip("/")}/'

        t = FAGet.interval - (time.time() - self.lastget)
        if t > 0:
            self.Log(f'FAGet get -> wait {t:.1f} secs')
            time.sleep(t)

        self.lastget = time.time()

        try:
            get = self.Session.get(url, params=params)
            self.Log(f'FAGet get -> get status:{get.ok}')

            return get if get.ok else None
        except:
            err = traceback.format_exception(*sys.exc_info())
            err = ['FAGet get -> error: '+e.strip().replace('\n', ' =') for e in err]
            self.Log(err)
            return None

    def getParse(self, url, **params):
        self.Log(f'FAGet getParse -> url:{url} params:{params}')
        get = self.get(url, **params)
        get = bs4.BeautifulSoup(get.text, 'lxml') if get else None

        self.Log(f'FAGet getParse -> {"success" if get else "fail"}')

        return get
