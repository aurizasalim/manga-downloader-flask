import json
import re
import subprocess
from jinja2 import Environment, FileSystemLoader


def run_crawler(crawler_name, **kwargs):
    """
    runs the crawler of crawler_name with the given kwargs
    returns a list of dicts of data
    """
    outfile = "results.json"
    #truncate the output file
    open(outfile, 'w').close()

    #handle arguments if any are given
    args = []
    if kwargs:
        args = ["-a"]
        for k, v in kwargs.iteritems():
            args.append("%s=%s" % (k, v))

    cmd = ["scrapy", "crawl", crawler_name, "--nolog"] + args + \
          ["-o", outfile, "-t", "jsonlines"]

    # block until completion
    subprocess.call(cmd)

    return [json.loads(x) for x in open(outfile)]


def extract_link(link_node):
    """returns (text, href) of the given link node"""
    return (link_node.xpath('text()').extract()[0],
            link_node.xpath('@href').extract()[0])


def jinja_template(template_path, **kwargs):
    """
    inits jinja and returns a template object from the given path
    kwargs is a dict of globals to add to the templates
    """
    jinja2 = Environment(loader=FileSystemLoader("templates"))
    #add the globals to jinja
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
        #textual name or special chapter
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
