from scrapy.selector import Selector
from scrapy.spider import Spider
from scrapy.utils.url import urljoin_rfc
from scrapy.http.request import Request

import datetime
import json

from models import Manga
from manga.items import MangaItem, MangaChapterItem, MangaImagesItem
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

    def parse(self, response):
        hxs = Selector(response)

        base_url = "http://www.mangareader.net"
        page_links = hxs.xpath(
                            "//select[@id='pageMenu']/option/@value").extract()

        item = MangaImagesItem()
        item["chapter_data"] = self.chapter_data
        item["total_images"] = len(page_links)
        item['image_urls'] = []

        #fetch the images from all the pages
        for p in page_links:
            page = urljoin_rfc(base_url, p)
            request = Request(page, callback=self.parse_img_url)
            request.meta['item'] = item  # pass the item to the callback
            yield request

        yield item

    def parse_img_url(self, response):
        """returns the image url given the response"""
        hxs = Selector(response)
        img_url = hxs.xpath("//img[@id='img']/@src").extract()[0]

        #use the item passed to the callback
        item = response.meta['item']
        item['image_urls'].append(img_url)
        return item
