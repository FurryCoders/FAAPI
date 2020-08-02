import re
import filetype

months = {
    "January": "01",
    "February": "02",
    "March": "03",
    "April": "04",
    "May": "05",
    "June": "06",
    "July": "07",
    "August": "08",
    "September": "09",
    "October": "10",
    "November": "11",
    "December": "12",
}

re_ext1 = re.compile(":</strong>.*")
re_ext2 = re.compile(".*<strong>")
re_ext3 = re.compile(".*</strong>( )*")
re_ext4 = re.compile("</div>.*")


class FASub:
    def __init__(self, sub, getBinary=None):
        if str(type(sub)) not in ("<class 'bs4.BeautifulSoup'>", "<class 'NoneType'>"):
            raise TypeError("sub needs to be of type bs4.BeautifulSoup")

        if getBinary and not callable(getBinary):
            raise TypeError("getBinary needs to be of type function")

        self.sub = sub
        self.getBinary = getBinary

        self.analyze()

    def __iter__(self):
        yield "id", self.id
        yield "title", self.title
        yield "author", self.author
        yield "date", self.date
        yield "keyw", self.keyw
        yield "category", self.category
        yield "species", self.species
        yield "gender", self.gender
        yield "rating", self.rating
        yield "desc", self.desc
        yield "filelink", self.filelink
        yield "fileext", self.fileext

    def analyze(self):
        if not self.sub:
            self.id = None
            self.title = None
            self.author = None
            self.date = None
            self.tags = None
            self.category = None
            self.species = None
            self.gender = None
            self.rating = None
            self.desc = None
            self.filelink = None
            self.fileext = None
            self.file = None

            return

        self.id = self.sub.find("meta", property="og:url")
        self.id = self.id.get("content", None) if self.id else None
        self.id = int(self.id.split("/")[-2]) if self.id else 0

        self.title = self.sub.find("h2", "submission-title-header")
        self.title = self.title.string if self.title else ""

        self.author = self.sub.find("div", "submission-artist-container")
        self.author = self.author.find("h2") if self.author else None
        self.author = self.author.string if self.author else ""

        self.date = self.sub.find("meta", {"name": "twitter:data1"})
        self.date = self.date.get("content", "").replace(",", "") if self.date else None
        self.date = self.date.split(" ") if self.date else None
        self.date = (
            f"{self.date[2]}-{months[self.date[0]]}-{self.date[1]:0>2}"
            if self.date
            else ""
        )

        self.tags = [k.string for k in self.sub.find_all("span", "tags")]
        self.tags = self.tags[0 : int(len(self.tags) / 2)]
        self.tags = sorted(set(self.tags), key=str.lower)

        extras_raw = self.sub.find("div", "sidebar-section-no-bottom")
        extras_raw = [str(e) for e in extras_raw.find_all("div")] if extras_raw else []
        extras = {}
        for e in extras_raw:
            e_typ = re_ext1.sub("", e)
            e_typ = re_ext2.sub("", e_typ)
            e_val = re_ext3.sub("", e)
            e_val = re_ext4.sub("", e_val)
            extras[e_typ.lower()] = e_val.replace("&gt;", ">")
        self.category = extras.get("category", "")
        self.species = extras.get("species", "")
        self.gender = extras.get("gender", "")

        self.rating = self.sub.find("meta", {"name": "twitter:data2"})
        self.rating = self.rating.get("content", "") if self.rating else ""

        self.desc = self.sub.find("div", "submission-description-container")
        self.desc = str(self.desc.prettify()) if self.desc else None
        self.desc = self.desc.split("</div>", 1)[-1] if self.desc else None
        self.desc = self.desc.rsplit("</div>", 1)[0] if self.desc else ""
        self.desc = self.desc.strip()

        self.filelink = self.sub.find("a", "button download-logged-in")
        self.filelink = self.filelink.get("href", "") if self.filelink else None
        self.filelink = "https:" + self.filelink if self.filelink else ""
        self.fileext = (
            self.filelink.split(".")[-1]
            if self.filelink and "." in self.filelink
            else None
        )
        self.file = bytes() if self.filelink else None

    def getFile(self, getBinary=None):
        if not self.filelink:
            return

        self.getBinary = getBinary if getBinary else self.getBinary

        if not self.getBinary:
            return
        elif not callable(self.getBinary):
            raise TypeError("getBinary needs to be of type function")

        self.file = self.getBinary(self.filelink)

        self.fileext = (
            filetype.guess_extension(self.file) if self.file else self.fileext
        )

        if self.fileext == None:
            self.fileext = self.filelink.split(".")[-1] if "." in self.filelink else ""
        elif self.fileext == "zip":
            self.fileext = (
                "docx" if self.filelink.split(".")[-1] == "docx" else self.fileext
            )
