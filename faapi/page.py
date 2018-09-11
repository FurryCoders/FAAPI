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

    def subParse(self, sub):
        self.Log(f'FAPage subParse -> sub:{bool(sub)}')
        if not sub:
            return None

        if type(sub) == list:
            if any(str(type(s)) != "<class 'bs4.element.Tag'>" for s in sub):
                raise TypeError('submissions need to be of type bs4.BeautifulSoup')
        elif str(type(sub)) != "<class 'bs4.element.Tag'>":
            raise TypeError('submission needs to be of type bs4.BeautifulSoup')

        if type(sub) != list:
            sub = [sub]

        for i in range(0, len(sub)):
            s = sub[i]

            s = {
                'id':     s['id'][4:],
                'title':  s.findAll('a')[-2]['title'],
                'author': s.findAll('a')[-1]['title'],
                'rating': s['class'][0][2:]
                }

            sub[i] = s

        return sub
