from utils import run_spider


for i, line in enumerate(run_spider(
    "mangareader_chapter",
    cache=False,
    # log=False,
    start_urls="http://www.mangareader.net/shingeki-no-kyojin",
)):
    print i, line
