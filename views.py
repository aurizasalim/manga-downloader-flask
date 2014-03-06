from flask import render_template, redirect, request
from flask.views import View

import datetime
import json
import tempfile

from app import app, db
from models import Manga
from utils import run_crawler


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
    manga_list = run_crawler(manga_source_name.lower())

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
    chap_list = run_crawler(crawler_name, manga_id=manga.id)

    chapters = []
    chap_list = sorted(chap_list,
                       key=lambda c: (int(c["date"]), c["name"]),
                       reverse=True)

    #context for json data that will be submitted later
    json_data = [dict(c, manga_id=manga_id, manga_site=manga.mangasite)
                 for c in chap_list]

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
        chapters = request.json
        #dump the data into a file so that it can be read by the scrapy image
        #crawler
        with tempfile.NamedTemporaryFile(delete=False) as fp:
            fp.write("\n".join(json.dumps(c) for c in chapters))
            fp.close()

            #TODO: groupby crawler
            mangasite = chapters[0]["manga_site"]
            #start fetching the images
            crawler_name = "%s_images" % mangasite.lower()
            run_crawler(crawler_name, chapter_data_file=fp.name)

            #TODO: update last_updated timestamp for manga object
        return "success"

    def is_run_complete(self, results):
        """determines if a run is completed given results from a crawler run"""
        for r in results:
            if r["total_images"] != len(r["image_urls"]):
                return False
        return True

app.add_url_rule('/manga/download/',
                 view_func=DownloadChapterView.as_view('manga_download'))


if __name__ == '__main__':
    db.create_all()
    app.run(debug=True)
