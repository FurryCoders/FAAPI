class FAPage():
    def __init__(self, logger=(lambda *x: None)):
        logger('FAPage -> init')
        self.Log = logger

    def pageFind(self, page, **kwargs):
        self.Log(f'FAPage pageFind -> kwargs:{kwargs}')
        if str(type(page)) not in ("<class 'bs4.BeautifulSoup'>", "<class 'NoneType'>"):
            raise TypeError('page needs to be of type bs4.BeautifulSoup')
        elif not kwargs:
            raise TypeError('kwargs canot be empty')

        if page:
            find = list(page.findAll(limit=1, **kwargs))
            self.Log(f'FAPage pageFind -> {len(find)} items')
            return find
        else:
            self.Log(f'FAPage pageFind -> fail')
            return None

    def pageFindAll(self, page, **kwargs):
        self.Log(f'FAPage pageFindAll -> kwargs:{kwargs}')
        if str(type(page)) not in ("<class 'bs4.BeautifulSoup'>", "<class 'NoneType'>"):
            raise TypeError('page needs to be of type bs4.BeautifulSoup')
        elif not kwargs:
            raise TypeError('kwargs canot be empty')

        if page:
            find = list(page.findAll(**kwargs))
            self.Log(f'FAPage pageFindAll -> {len(find)} items')
            return find
        else:
            self.Log(f'FAPage pageFindAll -> fail')
            return None
