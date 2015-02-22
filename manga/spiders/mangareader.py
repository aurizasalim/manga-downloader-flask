from scrapy.selector import Selector
from scrapy.utils.url import urljoin_rfc
from scrapy.http.request import Request

import datetime
import json

from .base import BaseSpider as Spider
from manga.items import MangaItem, MangaChapterItem, MangaImagesItem
from utils import extract_link


class MangaReaderSpider(Spider):
    name = "mangareader"
    allowed_domains = ["mangareader.net"]
    start_urls = [
        "http://www.mangareader.net/alphabetical"
    ]

    def parse(self, resp):
        hxs = Selector(resp)
        for manga in hxs.css("ul.series_alpha > li > a"):
            item = MangaItem()
            item['name'], item['link'] = extract_link(manga)
            yield item


class MangaReaderChapterSpider(Spider):
    name = "mangareader_chapter"
    allowed_domains = ["mangareader.net"]

    def parsedate(self, s):
        return datetime.datetime.strptime(s.strip(), "%m/%d/%Y").date()

    def parse(self, resp):
        hxs = Selector(resp)

        for row in hxs.xpath("//table[@id='listing']//tr"):
            item = MangaChapterItem()
            cells = row.xpath("td")
            if not cells:
                continue

            item['name'], item['link'] = extract_link(cells[0].xpath("a"))
            item['date'] = self.parsedate(
                                    cells[-1].xpath('text()').extract()[0])
            yield item


class MangaReaderImageSpider(Spider):
    name = "mangareader_images"

    def __init__(self, chapter_data_file):
        """
        chapter_urls_file is a file containing the chapters to download,
        one on each line
        """

        base_url = "http://www.mangareader.net"
        self.start_urls = []
        self.chapter_data = []
        with open(chapter_data_file) as fp:
            for chapter in fp:
                chapter = json.loads(chapter)
                self.chapter_data.append(chapter)
                self.start_urls.append(urljoin_rfc(base_url, chapter["link"]))

    def parse(self, resp):
        hxs = Selector(resp)

        base_url = "http://www.mangareader.net"
        page_links = hxs.xpath(
                            "//select[@id='pageMenu']/option/@value").extract()

        item = MangaImagesItem()
        item["chapter_url"] = resp.url
        item["chapter_name"] = hxs.xpath("//div[@id='mangainfo']//h1/text()")\
                                .extract()[0]
        item["total_images"] = len(page_links)
        item['image_urls'] = []

        # fetch the images from all the pages
        for i, p in enumerate(page_links):
            page = urljoin_rfc(base_url, p)
            request = Request(page, callback=self.parse_img_url)
            # pass the index of the image for reordering later
            request.meta['index'] = i
            request.meta['item'] = item  # pass the item to the callback
            yield request

        yield item

    def parse_img_url(self, resp):
        """returns the image url given the resp"""
        hxs = Selector(resp)
        img_url = hxs.xpath("//img[@id='img']/@src").extract()[0]

        # use the item passed to the callback
        item = resp.meta['item']
        # image_urls is a list of tuples so we can sort it in order later
        item['image_urls'].append((resp.meta["index"], img_url))
        return item
