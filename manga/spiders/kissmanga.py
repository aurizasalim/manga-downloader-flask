from scrapy.http.request import Request
from scrapy.selector import Selector
from scrapy.spider import Spider
from scrapy.utils.response import get_base_url
from scrapy.utils.url import urljoin_rfc

import datetime

from models import Manga
from manga.items import MangaItem, MangaChapterItem
from utils import extract_link


class KissManga(Spider):
    name = "kissmanga"
    allowed_domains = ["kissmanga.com"]
    start_urls = [
        "http://kissmanga.com/MangaList/"
    ]

    def parse(self, response):
        hxs = Selector(response)

        #handle pagination recursively
        base_url = get_base_url(response)
        pagination = hxs.xpath("//ul[@class='pager']/li/a"
                                "[contains(text(),'Next')]/@href").extract()
        if pagination:
            yield Request(urljoin_rfc(base_url, pagination[0]), self.parse)

        mangas = hxs.xpath("//table[@class='listing']/tr/td[1]/a")

        for manga in mangas:
            item = MangaItem()
            item['name'], item['link'] = extract_link(manga)
            yield item


class KissMangaChapterSpider(Spider):
    name = "kissmanga_chapter"
    allowed_domains = ["kissmanga.com"]

    def __init__(self, manga_id):
        base_url = "http://kissmanga.com"
        self.start_urls = [
            urljoin_rfc(base_url, Manga.query.get(int(manga_id)).link),
        ]

    #parses the date format
    def parsedate(self, s):
        return datetime.datetime.strptime(s.strip(), "%m/%d/%Y").date()

    def parse(self, response):
        hxs = Selector(response)

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
