# Define your item pipelines here
#
# Don't forget to add your pipeline to the ITEM_PIPELINES setting
# See: http://doc.scrapy.org/en/latest/topics/item-pipeline.html


from scrapy.contrib.pipeline.images import ImagesPipeline, ImageException
from cStringIO import StringIO
from PIL import Image, ImageOps


class MangaImagesPipeline(ImagesPipeline):
    """
    pipeline built on top of the scrapy images pipeline that handles conversion
    of images with extended options
    """

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

    def item_completed(self, results, item, info):
        item = super(KindlePipeline, self).item_completed(results, item, info)
        return item
