from scrapy import Selector

import datetime

from .base import BaseSpider as Spider
from manga.items import MangaItem, MangaChapterItem
from utils import extract_link


class MangaHere(Spider):
    name = "mangahere"
    allowed_domains = ["mangahere.com"]
    start_urls = [
        "http://www.mangahere.com/mangalist/"
    ]

    def parse(self, resp):
        hxs = Selector(resp)
        for manga in hxs.css("a.manga_info"):
            item = MangaItem()
            item['name'], item['link'] = extract_link(manga)
            yield item


class MangaHereChapterSpider(Spider):
    name = "mangahere_chapter"
    allowed_domains = ["mangahere.com"]

    def parsedate(self, s):
        s = s.lower()
        if s.lower() == "today":
            return datetime.date.today()
        elif s.lower() == "yesterday":
            return datetime.date.today() - datetime.timedelta(1)
        else:
            return datetime.datetime.strptime(s, "%b %d, %Y").date()

    def parse(self, resp):
        hxs = Selector(resp)
        for row in hxs.css("div.detail_list > ul > li"):
            item = MangaChapterItem()
            cells = row.xpath("span")
            if not cells:
                continue

            try:
                item['name'], item['link'] = extract_link(cells[0].xpath("a"))
                item['date'] = self.parsedate(
                                        cells[-1].xpath('text()').extract()[0])
                yield item
            except IndexError:
                pass
