# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: http://doc.scrapy.org/en/latest/topics/item-pipeline.html

import json

from scrapy.contrib.pipeline.images import ImagesPipeline, ImageException
from scrapy.exceptions import DropItem
from scrapy.http.request import Request
try:
    from cStringIO import StringIO
except ImportError:
    from StringIO import StringIO
from PIL import Image, ImageOps

from utils import jinja_template


class MangaImagesPipeline(ImagesPipeline):
    """
    pipeline built on top of the scrapy images pipeline that handles conversion
    of images with extended options
    """
    def has_all_images(self, item):
        """does the item contain all the image urls to be downloaded?"""
        image_urls = item.get(self.IMAGES_URLS_FIELD, [])
        return item.get("total_images", -1) == len(image_urls)

    def get_media_requests(self, item, info):
        image_urls = item.get(self.IMAGES_URLS_FIELD, [])

        #don't have all the images, don't bother
        if not self.has_all_images(item):
            image_urls = []
        return [Request(x) for x in image_urls]

    def get_images(self, response, request, info):
        path = self.file_path(request, response=response, info=info)
        orig_image = Image.open(StringIO(response.body))

        width, height = orig_image.size
        if width < self.MIN_WIDTH or height < self.MIN_HEIGHT:
            raise ImageException("Image too small (%dx%d < %dx%d)" %
                                 (width, height, self.MIN_WIDTH,
                                  self.MIN_HEIGHT))

        image, buf = self.convert_image(orig_image)
        yield path, image, buf

        #modified the thumbnail options to accept a dict of options
        for thumb_id, convert_opts in self.THUMBS.iteritems():
            thumb_path = self.thumb_path(request, thumb_id, response=response,
                                         info=info)
            thumb_image, thumb_buf = self.convert_image(image, **convert_opts)
            yield thumb_path, thumb_image, thumb_buf

    def convert_image(self, image, **kwargs):
        """
        kwargs is a list of options to specify how the image should be
        processed
        """
        WHITE = (255, 255, 255)
        if image.format == 'PNG' and image.mode == 'RGBA':
            #transparency color is white
            background = Image.new('RGBA', image.size, WHITE)
            background.paste(image, image)
            image = background.convert('RGB')
        elif image.mode != 'RGB':
            image = image.convert('RGB')

        #rotate the image if it is landscape
        if image.size[0] > image.size[1]:
            image.rotate(90)

        #do grayscale if needed
        if kwargs.get('grayscale', False):
            image = ImageOps.grayscale(image)

        #do the resize
        size = kwargs.get('size', image.size)
        image = image.copy()
        image.thumbnail(size, Image.ANTIALIAS)

        #center the resize image
        offset_x = max((size[0] - image.size[0]) / 2, 0)
        offset_y = max((size[1] - image.size[1]) / 2, 0)

        final = Image.new(mode='RGB', size=size, color=WHITE)
        final.paste(image, (offset_x, offset_y))

        buf = StringIO()
        final.save(buf, 'JPEG')
        return final, buf


class KindlePipeline(MangaImagesPipeline):
    """
    pipeline for handling images suitable for output to a kindle
    """
    def __init__(self, *args, **kwargs):
        super(KindlePipeline, self).__init__(*args, **kwargs)
        self.chapter_urls = set()

    def item_completed(self, results, item, info):
        #not part of the image pipeline, just continue
        if self.IMAGES_URLS_FIELD not in item:
            return item

        #make sure the item is complete
        if not self.has_all_images(item):
            raise DropItem("Item Incomplete")

        #don't bother processing twice
        if item["chapter_url"] in self.chapter_urls:
            raise DropItem("Item Duplicate")
        else:
            self.chapter_urls.add(item["chapter_url"])

        #got all the images, begin processing
        page_tmpl = jinja_template("mobi/page.html")
        thumb_pages = []
        for thumb_name in self.THUMBS.iterkeys():
            for i, data in enumerate(results):
                fname = data[1]["path"].split("/")[-1][:-4]
                #write the page for the image
                thumb_pages.append(
                    self.write_image_page(thumb_name, i, fname, page_tmpl)
                )

        #write the data out to the chapters file
        with open("chapters.json", "a") as chapters_file:
            chapters_file.write("%s\n" % json.dumps(dict(item=dict(item),
                                                         results=thumb_pages)))

        return item

    def write_image_page(self, thumb_name, thumb_no, fname, tmpl):
        """
        writes the image page and returns the path of the html file written to
        """
        #name of thumbnail html file
        thumb_page = 'thumbs/%s/%s.html' % (thumb_name, fname)

        buf = StringIO(tmpl.render({
            "image_no": thumb_no,
            "image_name": fname,
        }))
        self.store.persist_file(thumb_page, buf, None)
        return thumb_page
