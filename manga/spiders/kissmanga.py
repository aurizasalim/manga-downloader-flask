from scrapy.http.request import Request
from scrapy.selector import Selector
from scrapy.utils.response import get_base_url
from scrapy.utils.url import urljoin_rfc

import datetime

from .base import BaseSpider as Spider
from manga.items import MangaItem, MangaChapterItem
from utils import extract_link


class KissManga(Spider):
    name = "kissmanga"
    allowed_domains = ["kissmanga.com"]
    start_urls = [
        "http://kissmanga.com/MangaList/"
    ]

    def parse(self, resp):
        hxs = Selector(resp)

        # handle pagination recursively
        base_url = get_base_url(resp)
        for pagination in hxs.css("ul.pager a"):
            txt, url = extract_link(pagination)
            if txt.endswith("Next"):
                yield Request(urljoin_rfc(base_url, url), self.parse)

        mangas = hxs.xpath("//table[@class='listing']/tr/td[1]/a")

        for manga in mangas:
            item = MangaItem()
            item['name'], item['link'] = extract_link(manga)
            yield item


class KissMangaChapterSpider(Spider):
    name = "kissmanga_chapter"
    allowed_domains = ["kissmanga.com"]

    # parses the date format
    def parsedate(self, s):
        return datetime.datetime.strptime(s.strip(), "%m/%d/%Y").date()

    def parse(self, resp):
        hxs = Selector(resp)

        rows = hxs.xpath("//table[@class='listing']//tr")
        for row in rows:
            item = MangaChapterItem()

            cells = row.xpath("td")
            if not cells:
                continue

            try:
                item['name'], item['link'] = extract_link(cells.xpath("a")[0])

                dt = cells.xpath("text()")[-1]
                item["date"] = self.parsedate(dt.extract())
            except IndexError:
                continue
            except ValueError:
                continue

            yield item
