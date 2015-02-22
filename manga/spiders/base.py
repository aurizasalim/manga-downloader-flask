from scrapy import Spider


class BaseSpider(Spider):
    """
    Provides some base functionality such as getting arguments from the command
    line
    """

    def __init__(self, *args, **kwargs):
        super(BaseSpider, self).__init__(*args, **kwargs)
        self.kwargs = kwargs

        self.start_urls = self.get_kwarg("start_urls")
        if isinstance(self.start_urls, basestring):
            self.start_urls = [u.strip() for u in self.start_urls.split(",")]
        # handle the case of having empty strings within the url
        self.start_urls = [u for u in self.start_urls if u]

    def get_kwarg(self, name, default=None):
        """
        returns the requested scraper kwarg, searching the kwargs followed by
        self, None otherwise
        """
        return getattr(self, name, self.kwargs.get(name, default))

