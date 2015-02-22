import json
import re
import subprocess
from jinja2 import Environment, FileSystemLoader


def run_spider(crawler_name, log=False, cache=True, **kwargs):
    """
    runs the given scraper and returns the fetched data as a list of dicts
    """
    outfile = "results.json"
    open(outfile, 'w').close()  # truncate the output file

    cmd = ["scrapy", "crawl"]
    if not log:
        cmd.append("--nolog")
    cmd.append(crawler_name)

    # pass in extra keyword args as needed
    for k, v in kwargs.iteritems():
        cmd += ['-a', "%s=%s" % (k, v)]

    # enable the cache if needed
    if not cache:
        cmd += ["--set", "HTTPCACHE_ENABLED=0"]

    cmd += ["-t", "jsonlines", "-o", outfile]
    # print " ".join(cmd)

    subprocess.call(cmd)
    with open(outfile) as fp:
        return [json.loads(line) for line in fp]


def extract_link(link_node):
    """returns (text, href) of the given link node"""
    return (link_node.xpath('text()').extract()[0].strip(),
            link_node.xpath('@href').extract()[0].strip())


def jinja_template(template_path, **kwargs):
    """
    inits jinja and returns a template object from the given path
    kwargs is a dict of globals to add to the templates
    """
    jinja2 = Environment(loader=FileSystemLoader("templates"))
    # add the globals to jinja
    jinja2.globals.update(**kwargs)
    return jinja2.get_template(template_path)


def strip_punctuation(s):
    """strips the punctuation from the given string"""
    return re.sub(ur"\p{P}+", "", s)


def chapter_number(manga_name, chapter_name):
    """returns the chapter number as a int, float or string"""
    manga_name = strip_punctuation(manga_name).lower().split()
    chapter_name = strip_punctuation(chapter_name).lower().split()

    number = chapter_name[len(manga_name):]
    if len(number) == 1:
        number = float(number[0])
        if int(number) == number:
            return int(number)
        else:
            return number
    else:
        # textual name or special chapter
        return ' '.join(chapter_name.split()[len(manga_name):])


def chapter_number_sort_key(manga_name, chapter_name):
    """
    returns a tuple of (chapter_number, chapter_string)

    if the chapter_number is valid,
    chapter_number is a int / float, chapter_string is ""
    if not,
    chapter_number is -1, chapter_string is the textual name
    """
    chap_num = chapter_number(manga_name, chapter_name)
    if isinstance(chap_num, basestring):
        return (chap_num, "")
    else:
        return (-1, chap_num)
