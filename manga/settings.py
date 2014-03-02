# Scrapy settings for manga project
#
# For simplicity, this file contains only the most important settings by
# default. All the other settings are documented here:
#
#     http://doc.scrapy.org/en/latest/topics/settings.html
import os


BOT_NAME = 'manga'

SPIDER_MODULES = ['manga.spiders']
NEWSPIDER_MODULE = 'manga.spiders'

# Crawl responsibly by identifying yourself (and your website) on the user-agent
#USER_AGENT = 'manga (+http://www.yourdomain.com)'

HTTPCACHE_ENABLED = True
HTTPCACHE_STORAGE = "scrapy.contrib.httpcache.FilesystemCacheStorage"
HTTPCACHE_EXPIRATION_SECS = 60 * 60 * 24  # cache for a day

if HTTPCACHE_ENABLED:
    DOWNLOADER_MIDDLEWARES = {
        'scrapy.contrib.downloadermiddleware.httpcache.HttpCacheMiddleware': 900,
    }


#handle the image pipelines
ITEM_PIPELINES = {'manga.pipelines.KindlePipeline': 1}
IMAGES_STORE = os.path.abspath(os.path.join(os.curdir, "images"))
#modified the thumbnail options to accept a dict of options
IMAGES_THUMBS = {
    'kindle': {
        'size': (758, 1024),
        'grayscale': True,
    },
}
