import os
import json

import cfscrape
import requests

from .get  import FAGet
from .page import FAPage

class FASession():
    def __init__(self, cookies_f='', cookies_l=[], logger=(lambda *x: None), logger_warn=(lambda *x: None)):
        if type(cookies_f) != str:
            raise TypeError('cookies_f needs to be of type str')
        elif type(cookies_l) != list:
            raise TypeError('cookies_l needs to be of type list')
        elif any(type(cookie) != dict for cookie in cookies_l):
            raise TypeError('cookies_l needs to be a list of dicts')

        logger('FASession -> init')
        self.cookies_f = cookies_f
        self.cookies   = cookies_l
        self.Session   = None
        self.Log       = logger
        self.LogW      = logger_warn
        self.makeSession()
        logger('FASession -> init complete')

    def makeSession(self):
        self.Log('FASession makeSession -> start')
        if not self.ping('http://www.furaffinity.net'):
            self.Log('FASession makeSession -> failed ping')
            return

        if not self.cookies:
            if os.path.isfile(self.cookies_f):
                with open(self.cookies_f, 'r') as f:
                    try:
                        self.cookies = json.load(f)
                        self.Log('FASession makeSession -> read cookies file')
                    except:
                        self.Log('FASession makeSession -> failed cookies file')
                        return
            else:
                self.Log('FASession makeSession -> no cookies found')
                return

        self.cookies = [{'name': c['name'], 'value': c['value']} for c in self.cookies if type(c) == dict and 'name' in c and 'value' in c]

        self.Session = cfscrape.create_scraper()

        for cookie in self.cookies:
            self.Session.cookies.set(cookie['name'], cookie['value'])

        check_p = FAGet(self.Session, self.Log, self.LogW).getParse('/controls/settings/')
        check_p = FAPage(self.Log).pageFind(check_p, name='a', id='my-username')

        if not check_p:
            self.Log('FASession makeSession -> failed cookies check')
            self.Session = None

        self.Log(f'FASession makeSession -> {"success" if self.Session else "fail"}')

    def ping(self, url):
        try:
            requests.get(url, stream=True)
            self.Log('FASession ping -> True')
            return True
        except:
            self.Log('FASession ping -> False')
            return False
