import os
import json

import cfscrape
import requests

from .get import FAGet

default_cookies_f = 'FA.cookies.json'

class FASession():
    def __init__(self, cookies_f='', cookies_l=[], logger=(lambda *x: None)):
        logger('FASession -> init')
        self.cookies_f = cookies_f if cookies_f else default_cookies_f
        self.cookies   = cookies_l
        self.Session   = None
        self.Log       = logger

        self.makeSession()

    def makeSession(self):
        self.Log('FASession makeSession -> start')
        if not self.ping('http://www.furaffinity.net'):
            self.Log('FASession makeSession -> failed ping')
            return

        if not self.cookies and os.path.isfile(self.cookies_f):
            with open(self.cookies_f, 'r') as f:
                try:
                    self.cookies = json.load(f)
                except:
                    self.Log('FASession makeSession -> failed file')
                    return

        self.cookies = [{'name': c['name'], 'value': c['value']} for c in self.cookies if type(c) == dict and 'name' in c and 'value' in c]

        self.Session = cfscrape.create_scraper()

        for cookie in self.cookies:
            self.Session.cookies.set(cookie['name'], cookie['value'])

        check_p = FAGet(self.Log).pageFind(self.Session, '/controls/settings/', name='a', id='my-username')

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
