from scrapy.selector import Selector
from scrapy.spider import Spider
from scrapy.utils.url import urljoin_rfc

import datetime

from models import Manga
from manga.items import MangaItem, MangaChapterItem
from utils import extract_link


class MangaHere(Spider):
    name = "mangahere"
    allowed_domains = ["mangahere.com"]
    start_urls = [
        "http://www.mangahere.com/mangalist/"
    ]

    def parse(self, response):
        hxs = Selector(response)

        mangas = hxs.xpath("//div[@class='list_manga']/ul/li/a")

        items = []
        for manga in mangas:
            item = MangaItem()
            item['name'], item['link'] = extract_link(manga)
            items.append(item)
        return items


class MangaHereChapterSpider(Spider):
    name = "mangahere_chapter"
    allowed_domains = ["mangahere.com"]

    def __init__(self, manga_id):
        base_url = "http://www.mangahere.com"
        self.start_urls = [
            urljoin_rfc(base_url, Manga.query.get(int(manga_id)).link),
        ]

    #parses the date format
    def parsedate(self, s):
        s = s.lower()
        if s.lower() == "today":
            return datetime.date.today()
        elif s.lower() == "yesterday":
            return datetime.date.today() - datetime.timedelta(1)
        else:
            return datetime.datetime.strptime(s, "%b %d, %Y").date()

    def parse(self, response):
        hxs = Selector(response)

        rows = hxs.xpath("//div[@class='detail_list']//li")

        items = []
        for row in rows:
            item = MangaChapterItem()
            cells = row.xpath("span")
            if not cells:
                continue

            try:
                item['name'], item['link'] = extract_link(cells[0].xpath("a"))
                item['date'] = self.parsedate(
                                        cells[-1].xpath('text()').extract()[0])
                items.append(item)
            except IndexError:
                pass
        return items
