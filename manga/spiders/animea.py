import datetime

from scrapy.selector import Selector

from .base import BaseSpider as Spider
from manga.items import MangaItem, MangaChapterItem
from utils import extract_link


class AnimeA(Spider):
    name = "animea"
    allowed_domains = ["animea.net"]
    start_urls = [
        "http://manga.animea.net/series_old.php",
    ]

    def parse(self, resp):
        hxs = Selector(resp)

        for manga in hxs.css("a.tooltip_manga"):
            item = MangaItem()
            item['name'], item['link'] = extract_link(manga)
            yield item


class AnimeAChapterSpider(Spider):
    name = "animea_chapter"
    allowed_domains = ["animea.net"]

    # parses the date format
    def parsedate(self, s):
        # date is in number of days / weeks / months / years ago
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

    def parse(self, resp):
        hxs = Selector(resp)
        for row in hxs.css("ul.chapterlistfull > li"):
            item = MangaChapterItem()

            try:
                item["name"], item["link"] = extract_link(row.xpath("a")[0])

                dt = row.css("span.date::text")
                item["date"] = self.parsedate(dt.extract()[0])
            except IndexError:
                continue
            yield item
