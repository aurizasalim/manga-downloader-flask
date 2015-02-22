from flask import render_template, redirect, request
from flask.views import View

import datetime
import json
import os
import subprocess
import tempfile

from app import app, db
from models import Manga
from utils import run_spider, jinja_template, chapter_number_sort_key


MANGA_SOURCES = ["MangaReader", "MangaHere", "AnimeA", "KissManga"]


@app.context_processor
def manga_sources():
    return {"manga_sources": MANGA_SOURCES}


@app.route('/')
def home():
    return render_template('home.html')


@app.route('/site/<manga_source_name>/')
def show_site(manga_source_name):
    """displays all the manga available for a given source"""
    mangas = Manga.query.filter(Manga.mangasite == manga_source_name).\
                order_by(Manga.name).all()

    return render_template('manga_site.html',
                           manga_source_name=manga_source_name,
                           mangas=mangas)


@app.route('/site/<manga_source_name>/update/')
def update_site(manga_source_name):
    """displays all the manga available for a given source"""
    manga_list = run_spider(manga_source_name.lower())

    orig = Manga.query.filter(Manga.mangasite == manga_source_name)

    #save the manga which have last_updated set or are favs
    saved_info = orig.filter(
                    (Manga.fav == True) | (Manga.last_updated != None)).all()

    #create dicts from the newly added manga_list
    manga_list = [dict(m, mangasite=manga_source_name) for m in manga_list]

    for info in saved_info:
        #search the manga_list for the matching manga
        for m in manga_list:
            if m['name'] == info.name:
                m['fav'] = info.fav
                m['last_updated'] = info.last_updated
                break

    #delete all current manga entries
    orig.delete()
    db.session.commit()

    #add the newly fetched manga to the database
    db.session.add_all([Manga(**m) for m in manga_list])
    db.session.commit()

    return redirect("/site/%s/" % manga_source_name)


@app.route('/manga/<int:manga_id>/')
def manga_chapters(manga_id):
    """displays all the manga available for a given source"""
    manga = Manga.query.get(manga_id)

    crawler_name = "%s_chapter" % manga.mangasite.lower()
    chap_list = run_spider(crawler_name, manga_id=manga.id)

    chapters = []
    chap_list = sorted(chap_list,
                key=lambda c: chapter_number_sort_key(manga.name, c["name"]),
                reverse=True)

    #context for json data that will be submitted later
    json_data = [dict(c, manga_id=manga_id, manga_site=manga.mangasite,
                      manga_name=manga.name) for c in chap_list]

    #context for displaying the tables
    for chapter in chap_list:
        chapter["date"] = datetime.datetime.fromtimestamp(
                                                int(chapter["date"])).date()
        chapters.append(chapter)

    return render_template('manga_chapters.html',
                           manga=manga,
                           chapters=chapters,
                           json_data=json_data)


class DownloadChapterView(View):
    """downloads manga"""
    methods = ['POST']

    def dispatch_request(self):
        #clear the chapters file
        open("chapters.json", "w").close()

        #dump the data into a file so that it can be read by the scrapy image
        #crawler
        #TODO: groupby crawler
        chapters = request.json
        manga_name = chapters[0]["manga_name"]
        self.write_images_html(chapters)
        self.write_ncx(manga_name)
        self.write_opf(manga_name)
        self.write_mobi(manga_name)

        #TODO: update last_updated timestamp for manga object
        return "success"

    def write_images_html(self, chapters):
        """
        fetches the images and writes the corresponding html page for each
        image using the customized scrapy images pipeline

        takes the chapters data in the format from the request as an argument
        """
        with tempfile.NamedTemporaryFile(delete=False) as fp:
            fp.write("\n".join(json.dumps(c) for c in chapters))
            fp.close()

            mangasite = chapters[0]["manga_site"]
            #start fetching the images
            crawler_name = "%s_images" % mangasite.lower()
            run_spider(crawler_name, chapter_data_file=fp.name)

    def read_chapters_json(self, manga_name):
        """
        reads the chapters.json file and returns the chapters in chronological
        order
        """
        chapters = [json.loads(x) for x in open("chapters.json")]
        return sorted(chapters,
            key=lambda c: chapter_number_sort_key(manga_name,
                                                  c["item"]["chapter_name"]))

    def write_ncx(self, manga_name):
        """write the ncx file, using the data from chapters.json"""
        ncx_tmpl = jinja_template("mobi/ncx.xml")
        context = {
            "manga_name": manga_name,
            "chapters": [],
        }

        for c in self.read_chapters_json(manga_name):
            context["chapters"].append({
                "name": c["item"]["chapter_name"],
                "cover": c["results"][0]  # first page
            })

        with open("images/%s.ncx" % manga_name, "w") as fp:
            fp.write(ncx_tmpl.render(context))

    def write_opf(self, manga_name):
        """write the opf file, using the data from chapters.json"""
        opf_tmpl = jinja_template("mobi/opf.xml")

        context = {
            "manga_name": manga_name,
            "chapters": [],
        }
        for c in self.read_chapters_json(manga_name):
            context["chapters"].append({
                "name": c["item"]["chapter_name"],
                "pages": c["results"],
            })

        with open("images/%s.opf" % manga_name, "w") as fp:
            fp.write(opf_tmpl.render(context))

    def write_mobi(self, manga_name):
        #create the large mobi file with kindlegen named output.mobi
        opf = os.path.abspath("images/%s.opf" % manga_name)

        #run kindlegen
        subprocess.call(["kindlegen", "-c2", opf, "-o", "output.mobi"])

        #use kindlestrip to minimize file size
        subprocess.call(["python", "kindlestrip.py", "images/output.mobi",
                         "%s.mobi" % manga_name])


app.add_url_rule('/manga/download/',
                 view_func=DownloadChapterView.as_view('manga_download'))


if __name__ == '__main__':
    db.create_all()
    app.run(debug=True)
