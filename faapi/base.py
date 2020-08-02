from typing import List
from typing import Union

from .connection import cookies_load
from .connection import make_session
from .get import FAGet
from .page import FAPage
from .sub import FASub


class FAAPI:
    def __init__(self, cookies_f: str = "", cookies_l: List[dict] = None):
        cookies_l = [] if cookies_l is None else cookies_l

        self.session = make_session(cookies_load(cookies_f, cookies_l))
        self.Get = FAGet(self.session)
        self.Page = FAPage()

    def get(self, url: str, **params):
        return self.Get.get(url, **params)

    def getParse(self, url: str, **params):
        return self.Get.getParse(url, **params)

    def getSub(self, ID: Union[int, str], file=False):
        assert isinstance(ID, int) or (isinstance(ID, str) and ID.isdigit())

        sub = self.Get.getParse(f"/view/{ID}")
        sub = FASub(sub, getBinary=self.Get.getBinary)
        if file:
            sub.getFile()
        return sub

    def userpage(self, user: str):
        assert isinstance(user, str)

        page = self.Get.getParse(f"/user/{user}/")
        usrn = self.Page.pageFind(page, name="title")[0] if page else ""
        usrn = (
            usrn.text[12:21]
            if not usrn.text.lower().startswith("account disabled")
            else ""
        )
        desc = self.Page.pageFind(
            page, name="div", class_="userpage-layout-profile-container link-override"
        )
        desc = desc[0] if desc else ""

        return [usrn, desc]

    def gallery(self, user: str, page: int = 1):
        assert isinstance(user, str)
        assert isinstance(page, int) and page >= 1

        subs = self.Get.getParse(f"/gallery/{user}/{page}")

        titl = self.Page.pageFind(subs, name="title")[0].text
        if titl.lower().startswith("account disabled"):
            return [None, 0]

        subs = self.Page.pageFindAll(subs, name="figure") if subs else []

        return [self.Page.subParse(subs), page + 1]

    def scraps(self, user: str, page: int = 1):
        assert isinstance(user, str)
        assert isinstance(page, int) and page >= 1

        subs = self.Get.getParse(f"/scraps/{user}/{page}")

        titl = self.Page.pageFind(subs, name="title")[0].text
        if titl.lower().startswith("account disabled"):
            return [None, 0]

        subs = self.Page.pageFindAll(subs, name="figure") if subs else []

        return [self.Page.subParse(subs), page + 1]

    def favorites(self, user: str, page: str = ""):
        assert isinstance(user, str)
        assert isinstance(page, str)

        page = self.Get.getParse(f'/favorites/{user}/{page.strip("/")}')

        titl = self.Page.pageFind(page, name="title")[0].text
        if titl.lower().startswith("account disabled"):
            return [None, ""]

        subs = self.Page.pageFindAll(page, name="figure") if page else []
        next = (
            self.Page.pageFind(page, name="a", class_="button mobile-button right")
            if page
            else []
        )
        next = (next[0].get("href", ""))[11 + len(user):] if next else ""

        return [self.Page.subParse(subs), next]

    def search(self, **params):
        if "q" not in params:
            raise TypeError('cannot search with empty "q" parameter')
        elif any(type(v) not in (str, int) for v in params.values()):
            raise TypeError("params values must be of type string or int")

        page = self.Get.getParse("/search/", **params)

        subs = self.Page.pageFindAll(page, name="figure") if page else []
        next = (
            not bool(self.Page.pageFind(page, name="input", class_="button hidden"))
            if subs
            else False
        )
        next = params.get("page", 1) + 1 if next else 0

        return [self.Page.subParse(subs), next]

    def checkUser(self, user: str):
        assert isinstance(user, str)

        page = self.Get.getParse(f"/user/{user}/")
        titl = self.Page.pageFind(page, name="title")

        if not titl:
            return False
        elif titl[0].text.lower() == "system error":
            return False
        elif titl[0].text.lower().startswith("account disabled"):
            return False
        else:
            return True

    def checkSub(self, ID: Union[int, str]):
        assert isinstance(ID, int) or (isinstance(ID, str) and ID.isdigit())

        page = self.Get.getParse(f"/view/{ID}/")
        titl = self.Page.pageFind(page, name="title")

        if not titl:
            return False
        elif titl[0].text.lower() == "system error":
            return False
        else:
            return True
