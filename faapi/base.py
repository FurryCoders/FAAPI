from inspect  import getargspec

from .session import FASession
from .get     import FAGet
from .page    import FAPage
from .sub     import FASub

class FAAPI():
    def __init__(self, cookies_f='', cookies_l=[], **loggers):
        if any(not callable(log) for log in loggers.values()):
            raise TypeError('logger arguments need to be functions')
        elif any(len(getargspec(log)[0]) < 1 for log in loggers.values()):
            raise TypeError('logger functions need to accept at least one argument')

        loggers.get('logger_norm', (lambda *x: None))('FAAPI -> init')
        self.Log     = loggers.get('logger_norm', (lambda *x: None))
        self.LogV    = loggers.get('logger_verb', (lambda *x: None))
        self.LogW    = loggers.get('logger_warn', (lambda *x: None))
        self.Session = FASession(cookies_f, cookies_l, self.LogV, self.LogW)
        self.Get     = FAGet(self.Session.Session, self.LogV, self.LogW)
        self.Page    = FAPage(self.LogV)
        self.LogV('FAAPI -> init complete')

    def get(self, url, **params):
        self.Log(f'FAAPI get -> {url} {params}')
        return self.Get.get(url, **params)

    def getParse(self, url, **params):
        self.Log(f'FAAPI getParse -> {url} {params}')
        return self.Get.getParse(url, **params)

    def getSub(self, ID, file=False):
        self.Log(f'FAAPI getSub -> ID:{ID}')
        if type(ID) != int and not str(ID).isdigit():
            raise TypeError('ID needs to be an integer or string of integers')

        sub = self.Get.getParse(f'/view/{ID}')
        sub = FASub(sub, getBinary=self.Get.getBinary, logger=self.LogV)
        if file:
            sub.getFile()
        return sub

    def userpage(self, user):
        self.Log(f'FAAPI userpage -> user:{user}')

        page = self.Get.getParse(f'/user/{user}/')
        page = self.Page.pageFind(page, name='div', class_='userpage-layout-profile-container link-override')[0] if page else ''

        return page

    def gallery(self, user, page=1):
        self.Log(f'FAAPI gallery -> user:{user} page:{page}')
        if type(page) != int or page < 1:
            raise TypeError('page argument needs to be an integer greater than 1')

        subs = self.Get.getParse(f'/gallery/{user}/{page}')
        subs = self.Page.pageFindAll(subs, name='figure') if subs else []

        return [self.Page.subParse(subs), page+1]

    def scraps(self, user, page=1):
        self.Log(f'FAAPI scraps -> user:{user} page:{page}')
        if type(page) != int or page < 1:
            raise TypeError('page argument needs to be an integer greater than 1')

        subs = self.Get.getParse(f'/scraps/{user}/{page}')
        subs = self.Page.pageFindAll(subs, name='figure') if subs else []

        return [self.Page.subParse(subs), page+1]

    def favorites(self, user, page=''):
        self.Log(f'FAAPI favorites -> user:{user} page:{page}')
        if type(page) != str:
            raise TypeError('page argument needs to be string')

        page = self.Get.getParse(f'/favorites/{user}/{page.strip("/")}')

        subs = self.Page.pageFindAll(page, name='figure') if page else []
        next = self.Page.pageFind(page, name='a', class_='button mobile-button right') if page else []
        next = (next[0].get('href', ''))[11+len(user):] if next else ''

        return [self.Page.subParse(subs), next]

    def search(self, q='', **params):
        self.Log(f'FAAPI search -> params:{params}')
        if not q and not 'q' in params:
            raise TypeError('cannot search with empty "q" parameter')

        params['q'] = params.get('q', q)

        page = self.Get.getParse('/search/', **params)

        subs = self.Page.pageFindAll(page, name='figure') if page else []
        next = not bool(self.Page.pageFind(page, name='input', class_='button hidden')) if page else False
        next = params.get('page', 1)+1 if next else 0

        return [self.Page.subParse(subs), next]
