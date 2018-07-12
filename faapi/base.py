from .session import FASession
from .get     import FAGet
from .page    import FAPage

class FAAPI():
    def __init__(self, cookies_f='', cookies_l=[], logger_norm=(lambda *x: None), logger_verb=(lambda *x: None)):
        logger_norm('FAAPI -> init')
        self.Session = FASession(cookies_f, cookies_l, logger_verb)
        self.Get     = FAGet(logger_verb)
        self.Page    = FAPage(logger_verb)
        self.Log     = logger_norm

    def get(self, url, **params):
        self.Log(f'FAAPI get -> {url} {params}')
        return self.Get.get(self.Session.Session, url, **params)

    def getParse(self, url, **params):
        self.Log(f'FAAPI getParse -> {url} {params}')
        return self.Get.getParse(self.Session.Session, url, **params)

    def gallery(self, user, page=1):
        self.Log(f'FAAPI gallery -> user:{user} page:{page}')
        if type(page) != int or page < 1:
            raise TypeError('page argument needs to be an integer greater than 1')

        page = self.Get.getParse(self.Session.Session, f'/gallery/{user}/{page}')
        page = self.Page.pageFindAll(page, name='figure') if page else []

        return [page, f'/gallery/{user}/{page+1}']

    def scraps(self, user, page=1):
        self.Log(f'FAAPI scraps -> user:{user} page:{page}')
        if type(page) != int or page < 1:
            raise TypeError('page argument needs to be an integer greater than 1')

        page = self.Get.getParse(self.Session.Session, f'/scraps/{user}/{page}')
        page = self.Page.pageFindAll(page, name='figure') if page else []

        return [page, f'/scraps/{user}/{page+1}']

    def favorites(self, user, page=''):
        self.Log(f'FAAPI favorites -> user:{user} page:{page}')
        if type(page) != str:
            raise TypeError('page argument needs to be strs')

        page = self.Get.getParse(self.Session.Session, f'/favorites/{user}/{page.strip("/")}')

        subs = self.Page.pageFindAll(page, name='figure') if page else []
        next = self.Page.pageFind(page, name='a', class_='button mobile-button right') if page else []
        next = (next[0].get('href', ''))[11+len(user):] if next else ''

        return [subs, next]

    def search(self, q='', **params):
        self.Log(f'FAAPI search -> params:{params}')
        if not q and not params.get('q', ''):
            raise TypeError('cannot search with empty "q" parameter')

        params['q'] = params.get('q', q)

        page = self.Get.getParse(self.Session.Session, '/search/', **params)

        subs = self.Page.pageFindAll(page, name='figure') if page else []
        next = self.Page.pageFind(page, name='input', class_='button') if page else ''
        next = bool(next)

        return [subs, next]
