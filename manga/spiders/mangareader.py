from scrapy.selector import Selector
from scrapy.spider import Spider
from scrapy.utils.url import urljoin_rfc

import datetime

from models import Manga
from manga.items import MangaItem, MangaChapterItem
from utils import extract_link


class MangaReaderSpider(Spider):
    name = "mangareader"
    allowed_domains = ["mangareader.net"]
    start_urls = [
        "http://www.mangareader.net/alphabetical"
    ]

    def parse(self, response):
        hxs = Selector(response)

        mangas = hxs.xpath("//div[@class='content_bloc2']/"
                            "div[@class='series_col']//li/a")
        items = []
        for manga in mangas:
            item = MangaItem()
            item['name'], item['link'] = extract_link(manga)
            items.append(item)
        return items


class MangaReaderChapterSpider(Spider):
    name = "mangareader_chapter"
    allowed_domains = ["mangareader.net"]

    def __init__(self, manga_id):
        base_url = "http://www.mangareader.net"
        self.start_urls = [
            urljoin_rfc(base_url, Manga.query.get(int(manga_id)).link),
        ]

    #parses the date format
    def parsedate(self, s):
        return datetime.datetime.strptime(s.strip(), "%m/%d/%Y").date()

    def parse(self, response):
        hxs = Selector(response)

        rows = hxs.xpath("//table[@id='listing']//tr")

        items = []
        for row in rows:
            item = MangaChapterItem()
            cells = row.xpath("td")
            if not cells:
                continue

            item['name'], item['link'] = extract_link(cells[0].xpath("a"))
            item['date'] = self.parsedate(
                                    cells[-1].xpath('text()').extract()[0])
            items.append(item)
        return items
