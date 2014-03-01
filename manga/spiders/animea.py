from scrapy.http.request import Request
from scrapy.selector import Selector
from scrapy.spider import Spider
from scrapy.utils.response import get_base_url
from scrapy.utils.url import urljoin_rfc

import datetime

from models import Manga
from manga.items import MangaItem, MangaChapterItem
from utils import extract_link


class AnimeA(Spider):
    name = "animea"
    allowed_domains = ["animea.net"]
    start_urls = [
        "http://manga.animea.net/browse.html"
    ]

    def parse(self, response):
        hxs = Selector(response)

        #handle pagination recursively
        pagination = hxs.xpath("//ul[@class='paging']/li/a"
                                "[contains(text(),'Next')]/@href").extract()
        if pagination:
            yield Request(pagination[0], self.parse)

        mangas = hxs.xpath("//a[contains(@class,'manga_title')]")

        for manga in mangas:
            item = MangaItem()
            item['name'], item['link'] = extract_link(manga)
            yield item


class AnimeAChapterSpider(Spider):
    name = "animea_chapter"
    allowed_domains = ["animea.net"]

    def __init__(self, manga_id):
        base_url = "http://manga.animea.net"
        self.start_urls = [
            urljoin_rfc(base_url, Manga.query.get(int(manga_id)).link),
        ]

    #parses the date format
    def parsedate(self, s):
        #date is in number of days / weeks / months / years ago
        s = s.strip().lower().split()
        val = int(s[0])
        unit = s[1]
        if "day" in unit:
            delta = val
        elif "week" in unit:
            delta = val * 7
        elif "month" in unit:
            delta = val * 30
        elif "year" in unit:
            delta = val * 365
        else:
            raise ValueError("Unrecognised unit: %s" % unit)

        return datetime.date.today() - datetime.timedelta(delta)

    def parse(self, response):
        hxs = Selector(response)

        #check for the presence of the 'mature' warning
        warning = hxs.xpath("//ul[@class='chapters_list']/li[@class='notice']"
                            "//a/@href").extract()
        if warning:

            yield Request(urljoin_rfc(get_base_url(response), warning[0]),
                          self.parse)

        rows = hxs.xpath("//ul[@class='chapters_list']/li")
        for row in rows:
            item = MangaChapterItem()

            try:
                item["name"], item["link"] = extract_link(row.xpath("a")[0])

                dt = row.xpath(".//span[@class='right']/text()")
                item["date"] = self.parsedate(dt.extract()[0])
            except IndexError:
                continue

            yield item
