class FAPage:
    def __init__(self):
        pass

    def pageFind(self, page, **kwargs):
        if str(type(page)) not in ("<class 'bs4.BeautifulSoup'>", "<class 'NoneType'>"):
            raise TypeError("page needs to be of type bs4.BeautifulSoup")
        elif not kwargs:
            raise TypeError("kwargs canot be empty")

        if page:
            find = list(page.findAll(limit=1, **kwargs))
            return find
        else:
            return None

    def pageFindAll(self, page, **kwargs):
        if str(type(page)) not in ("<class 'bs4.BeautifulSoup'>", "<class 'NoneType'>"):
            raise TypeError("page needs to be of type bs4.BeautifulSoup")
        elif not kwargs:
            raise TypeError("kwargs canot be empty")

        if page:
            find = list(page.findAll(**kwargs))
            return find
        else:
            return None

    def subParse(self, sub):
        if not sub:
            return []

        if type(sub) == list:
            if any(str(type(s)) != "<class 'bs4.element.Tag'>" for s in sub):
                raise TypeError("submissions need to be of type bs4.BeautifulSoup")
        elif str(type(sub)) != "<class 'bs4.element.Tag'>":
            raise TypeError("submission needs to be of type bs4.BeautifulSoup")

        if type(sub) != list:
            sub = [sub]

        for i in range(0, len(sub)):
            s = sub[i]

            s = {
                "id": s["id"][4:],
                "title": s.findAll("a")[-2]["title"],
                "author": s.findAll("a")[-1]["title"],
                "rating": s["class"][0][2:],
            }

            sub[i] = s

        return sub
