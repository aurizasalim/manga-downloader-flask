import datetime
import json
import subprocess
from urlparse import urljoin

from app import db
from models import Manga

#TODO: possible other sources: MangaDog, KissManga
# chapter = namedtuple('chapter', 'text url date')


class MangaSource(object):
    """
    Abstract base class for website sources for fetching managa

    Optional attributes:
        manga_list_start: starting index of manga list
        manga_list_end: ending index of manga list
        manga_list_step: step index of manga list

        chapter_list_elem_start: starting index of manga list elements
        chapter_list_elem_end: ending index of manga list elements
        chapter_list_elem_step: step index of manga list elements

        chapter_list_start: starting index of manga list
        chapter_list_end: ending index of manga list
        chapter_list_step: step index of manga list

    Required attributes:
        manga_list_xpath: xpath to get manga links from the manga list
        chapter_list_xpath: xpath to get chapter links from the chapter list
    """

    def __init__(self):
        cls_name = self.__class__.__name__
        self.query = Manga.query.filter(Manga.mangasite == cls_name)

        # #check for the presence of required attributes
        # required_attrs = ["manga_list_xpath", "chapter_list_xpath",
        #                   "image_xpath"]
        # for a in required_attrs:
        #     if not hasattr(self, a):
        #         raise NotImplementedError("%s: Attribute %s is required." %
        #                                   (self.__class__.__name__, a))

    # def _get_slice(self, arr, attr_name):
    #     """
    #     utility method, returns a slice of an iterable given an attr name
    #     the convention is to name the attrs to be attr_name_(start|end|step)
    #     """

    #     s = slice(
    #         getattr(self, "%s_start" % attr_name, None),
    #         getattr(self, "%s_end" % attr_name, None),
    #         getattr(self, "%s_step" % attr_name, None),
    #     )
    #     return arr.__getitem__(s)

    # def get(self, url, **kwargs):
    #     """gets a Webpage object given the url and the given kwargs"""
    #     return Webpage(url, **kwargs)

    # def get_mangas_urls(self):
    #     """
    #     returns a list of list page urls
    #     only returns a single list url by default, override if pagination is
    #     required
    #     """
    #     return [urljoin(self.url, self.list_url)]

    # def get_mangas_pages(self, **kwargs):
    #     """fetches and returns the list url as a Webpage object"""
    #     list_urls = self.get_mangas_urls()
    #     #single url, default case
    #     if len(list_urls) == 1:
    #         return [self.get(list_urls[0], **kwargs)]
    #     #multiple urls, fetch them async
    #     else:
    #         #go thru the pages, concurrent fetch using greenlets
    #         jobs = [gevent.spawn(self.get, u, **kwargs) for u in list_urls]
    #         gevent.joinall(jobs)
    #         return [job.value for job in jobs]

    # def parse_manga_list(self, page):
    #     """parses a Webpage object and returns a list of link namedtuples"""
    #     return page.iter_links(self.manga_list_xpath)

    def get_mangas(self):
        """returns the list of mangas for this manga source"""
        return self.query.order_by(Manga.name).all()

    def update_mangas(self):
        """updates the list of manga"""
        manga_list = self.fetch_mangas()

        #save the manga which have last_updated set or are favs
        saved_info = self.query.filter((Manga.fav == True) |
                (Manga.last_updated != None)).all()

        #create dicts from the newly added manga_list
        manga_list = [dict(m, mangasite=self.__class__.__name__)
                      for m in manga_list]

        for saved_info in saved_info:
            #search the manga_list for the matching manga
            for m in manga_list:
                if m['name'] == saved_info.name:
                    m['fav'] = saved_info.fav
                    m['last_updated'] = saved_info.last_updated
                    break

        #delete all current manga entries
        self.query.delete()
        db.session.commit()

        #add the newly fetched manga to the database
        db.session.add_all([Manga(**m) for m in manga_list])
        db.session.commit()

    # def search_manga_list(self, keyword):
    #     """searches the manga list and returns all the matches"""
    #     return self.query.filter(Manga.name.contains(keyword)).all()

    # def get_chapter_list_elements(self, manga_url):
    #     """returns a list of chapter lxml Elements given the url"""
    #     manga_url = urljoin(self.url, manga_url)
    #     elems = self.get(manga_url).xpath(self.chapter_list_xpath)
    #     return self._get_slice(elems, "chapter_list_elem")

    # def get_chapter_list(self, manga_url):
    #     """returns a list of chapter namedtuples given the url"""
    #     chapters = []
    #     for chap in self.get_chapter_list_elements(manga_url):
    #         args = self.parse_chapter(chap)
    #         if args is not None:
    #             chapters.append(chapter(*args))
    #     return self._get_slice(chapters, "chapter_list")

    # def parse_chapter(self, chapter):
    #     """
    #     returns a list of chapter text, chapter url and date, given an lxml
    #     Element
    #     if None is returned, then this chapter will be ignored
    #     """
    #     raise NotImplementedError("%s: parse_chapter is required." %
    #                                 self.__class__.__name__)

    # #gets a manga based on the exact manga title
    # def get_manga(self, title):
    #     return self.query.filter(Manga.name == title).one()

    # def is_valid_image(self, imgurl):
    #     #do not include useless files like credits or recruitment
    #     garbage = ("credits", "thanks", "recruit", "cover", "seen",
    #                 "xxxhomeunixxxx")
    #     for x in garbage:
    #         if x in imgurl.lower():
    #             return False
    #     return True

    # def get_image_page_urls(self, chapter_page):
    #     """
    #     returns a list of urls of the pages containg the images, given the
    #     chapter url
    #     """
    #     raise NotImplementedError("%s: get_image_page_urls is required." %
    #                                 self.__class__.__name__)

    # def get_images(self, chapter):
    #     """returns a list of image urls for downloading"""
    #     chapter_url = urljoin(self.url, chapter.url)
    #     chapter_page = self.get(chapter_url)
    #     img_links = self.get_image_page_urls(chapter_page)

    #     #get the image urls async
    #     img_urls = [gevent.spawn(self.get, url) for url in img_links]
    #     gevent.joinall(img_urls)
    #     return [self.get_image_src(u.value) for u in img_urls]

    # def get_image_src(self, img_page):
    #     """
    #     returns the image src of the scan given the url of the containing page
    #     """
    #     return img_page.xpath(self.image_xpath)[0].attrib["src"]

    # #takes the url of an "image", download (process) the url if necessary
    # def download_image(self, url, fname):
    #     Webpage(url).download(fname)

    # @property
    # def manga_list(self):
    #     return self.query.all()


class MangaReader(MangaSource):
    url = "http://www.mangareader.net/"

    def fetch_mangas(self):
        crawler_name = self.__class__.__name__.lower()
        subprocess.Popen(["scrapy", "crawl", crawler_name, "-o",
                          "results.json", "-t", "jsonlines"])
        return [json.loads(x) for x in open("results.json").readlines()]

#     list_url = "/alphabetical"
#     manga_list_xpath = "//div.content_bloc2/div.series_col//li/a"
#     chapter_list_xpath = "//table#listing//tr"
#     chapter_list_elem_start = 1
#     chapter_list_step = -1
#     image_xpath = "//img#img"

#     #parses the date format
#     def parsedate(self, s):
#         return datetime.datetime.strptime(s, "%m/%d/%Y").date()

#     def parse_chapter(self, chapter):
#         title, date = chapter.getchildren()
#         title = title.xpath("a").pop()
#         return (title.text, title.attrib["href"], self.parsedate(date.text))

#     def get_image_page_urls(self, chapter_page):
#         return [urljoin(self.url, x.attrib["value"]) for x in
#                 chapter_page.xpath("//select#pageMenu/option")]


# class AnimeA(MangaSource):
#     url = "http://manga.animea.net/"
#     list_url = "/browse.html"
#     manga_list_xpath = "//ul.mangalist_plain/li/a"
#     chapter_list_xpath = "//ul.chapters_list/li"
#     chapter_list_elem_start = 1
#     image_xpath = "//img.mangaimg"

#     def get_mangas_urls(self):
#         """paginated, so have loop thru all the pages to get the manga list"""
#         list_url = urljoin(self.url, self.list_url)
#         #first get nav element at top of page, then find the max element
#         total_pages = self.get(list_url).iter_links("//ul.paging/li/a")
#         #last element is the next page, second last is the last page
#         total_pages = int(total_pages[-2].text)
#         return ["%s?listing=plain&page=%s" % (list_url, p) \
#                 for p in range(total_pages)]

#     #parses the date format
#     def parsedate(self, s):
#         #date is in number of days / weeks / months / years ago
#         s = s.lower().split()
#         val = int(s[0])
#         unit = s[1]
#         if "day" in unit:
#             delta = val
#         elif "week" in unit:
#             delta = val * 7
#         elif "month" in unit:
#             delta = val * 30
#         elif "year" in unit:
#             delta = val * 365
#         else:
#             raise ValueError("Unrecognised unit: %s" % unit)

#         return datetime.date.today() - datetime.timedelta(delta)

#     def parse_chapter(self, chapter):
#         title = chapter.xpath("a").pop()
#         date = chapter.xpath("div/span[@class='right']").pop().text
#         return (title.text, title.attrib["href"], self.parsedate(date))

#     def get_image_page_urls(self, chapter_page):
#         #get the urls of the pages from select box at top
#         pages = chapter_page.xpath("//div.navigation//select/option")
#         img_links = []
#         for p in pages:
#             img_links.append(chapter_page.url.replace(".html",
#                                         "-page-%s.html" % p.attrib["value"]))
#         return img_links


# class OurManga(MangaSource):
#     """
#     NOTE: OurManga does not show the date when chapters are posted, so
#     last_updated of any manga is always None
#     needless to say, updating will not work with OurManga
#     """
#     url = "http://www.ourmanga.com/"
#     list_url = "/directory/"
#     manga_list_xpath = "//div.m_s_title/a"
#     manga_list_start = 1
#     chapter_list_xpath = "//div#manga_nareo/div/div[1]/a"
#     chapter_list_start = 1
#     image_xpath = "//div.inner_full_view//img"

#     def parse_chapter(self, chapter):
#         return (chapter.text, chapter.attrib["href"], None)

#     def get_image_page_urls(self, chapter_page):
#         #gotta fetch a stupid intermediary page
#         chap_url1 = chapter_page.iter_links("//div#Summary/p[2]/a[2]").pop().\
#                     url
#         pages = self.get(chap_url1).xpath("//select[@name='page']/option")
#         return [urljoin(chap_url1, p.attrib["value"]) for p in pages]


# class MangaHere(MangaSource):
#     url = "http://www.mangahere.com/"
#     list_url = "/mangalist/"
#     manga_list_xpath = "//div.list_manga//a.manga_info"
#     chapter_list_xpath = "//div.detail_list//li"
#     chapter_list_elem_end = -1
#     image_xpath = "//img#image"

#     def parse_manga_list(self, page):
#         manga_info = page.xpath(self.manga_list_xpath)
#         return [link(m.text_content(), m.attrib["href"]) for m in manga_info]

#     #parses the date format
#     def parsedate(self, s):
#         if s.lower() == "today":
#             return datetime.date.today()
#         elif s.lower() == "yesterday":
#             return datetime.date.today() - datetime.timedelta(1)
#         else:
#             return datetime.datetime.strptime(s, "%b %d, %Y").date()

#     def parse_chapter(self, chapter):
#         try:
#             a = chapter.xpath("span/a")[0]
#             dt = self.parsedate(chapter.xpath("span[@class='right']")[0].text)
#             return (a.text.strip(), a.attrib["href"], dt)
#         except IndexError:
#             return None

#     def get_image_page_urls(self, chapter_page):
#         chap_url = chapter_page.url
#         pages = len(self.get(chap_url).xpath("//select.wid60")[0])
#         return [urljoin(chap_url, "%s.html" % p) for p in range(1, pages + 1)]


# class KissManga(MangaSource):
#     url = "http://kissmanga.com/"
#     list_url = "/MangaList"
#     manga_list_xpath = "//table.listing//tr/td[1]/a"
#     manga_list_start = 1
#     chapter_list_xpath = "//table.listing//tr"
#     chapter_list_elem_start = 2
#     image_xpath = "//div#divImage/p/img"

#     def get_mangas_urls(self):
#         """paginated, so have loop thru all the pages to get the manga list"""
#         list_url = urljoin(self.url, self.list_url)
#         #first get nav element at top of page, then find the last page link
#         l = self.get(list_url).xpath("//ul.pager/li").pop()
#         total_pages = int(l.xpath("a").pop().attrib["href"].split("=").pop())
#         return ["%s?page=%s" % (list_url, p) for p in
#                 range(1, total_pages + 1)]

#     def parsedate(self, s):
#         return datetime.datetime.strptime(s, "%m/%d/%Y").date()

#     def parse_chapter(self, chapter):
#         title, dt = chapter.xpath("td")
#         title = title.xpath("a").pop()
#         return (title.text.strip(), title.attrib["href"],
#                 self.parsedate(dt.text.strip()))

#     def get_images(self, chapter):
#         #all the images are on a single page and loaded via javascript
#         #parse the javascript, ugly, but it works
#         chapter_url = urljoin(self.url, chapter.url)
#         chapter_page = self.get(chapter_url)
#         img_urls = []
#         for line in str(chapter_page).splitlines():
#             line = line.strip()
#             if line.startswith("lstImages.push"):
#                 image_url = line.split('"')[-2].split("?")[0]
#                 img_urls.append(image_url+"?imgmax=2000")
#         return img_urls

# if __name__ == '__main__':
#     from pprint import pprint

#     # for mangasource in [MangaReader, AnimeA, OurManga, MangaHere]:
#     for mangasource in [KissManga]:
#         m = mangasource()
#         m.update_mangas()
#         bleach = m.search_manga_list("bleach")[0]
#         chap_list = m.get_chapter_list(bleach.link)
#         latest_chap = chap_list[0]
#         pprint(m.get_images(latest_chap))
