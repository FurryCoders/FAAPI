from .session import FASession
from .get     import FAGet

class FAAPI():
    def __init__(self, cookies_f='', cookies_l=[], logger_norm=(lambda *x: None), logger_verb=(lambda *x: None)):
        logger_norm('FAAPI -> init')
        self.Session = FASession(cookies_f, cookies_l, logger_verb)
        self.Get     = FAGet(logger_verb)
        self.Log     = logger_norm

    def get(self, url, **params):
        self.Log(f'FAAPI get -> {url} {params}')
        return self.Get.get(self.Session.Session, url, **params)

    def getParse(self, url, **params):
        self.Log(f'FAAPI getParse -> {url} {params}')
        return self.Get.getParse(self.Session.Session, url, **params)
