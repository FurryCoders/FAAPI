import requests
import bs4
import time

import traceback, sys

class FAGet():
    base_url = 'https://www.furaffinity.net/'
    interval = 12
    throttle = 100*1024

    def __init__(self, Session, logger=(lambda *x: None), logger_warn=(lambda *x: None)):
        logger('FAGet -> init')
        self.Session = Session
        self.lastget = -FAGet.interval
        self.Log     = logger
        self.LogW    = logger_warn

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
            self.LogW(err)
            return None

    def getParse(self, url, **params):
        self.Log(f'FAGet getParse -> url:{url} params:{params}')
        get = self.get(url, **params)
        get = bs4.BeautifulSoup(get.text, 'lxml') if get else None

        self.Log(f'FAGet getParse -> {"success" if get else "fail"}')

        return get

    def getBinary(self, url):
        self.Log(f'FAGet getBinary -> url:{url}')

        try:
            file_stream = self.Session.get(url, stream=True)
            file_binary = bytes()

            self.Log(f'FAGet getBinary -> stream status:{file_stream.ok}')

            if not file_stream.ok:
                file_stream.close()
                return file_binary

            for chunk in file_stream.iter_content(chunk_size=1024):
                file_binary += chunk
                time.sleep(1/(self.throttle/1024))

            self.Log(f'FAGet getBinary -> success')
            return file_binary
        except:
            err = traceback.format_exception(*sys.exc_info())
            err = ['FAGet get -> error: '+e.strip().replace('\n', ' =') for e in err]
            self.LogW(err)
            return bytes()
