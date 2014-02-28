from flask import render_template, redirect

import mangasource
from app import app, db


@app.context_processor
def manga_sources():
    manga_sources = []
    for obj in mangasource.__dict__.values():
        try:
            if issubclass(obj, mangasource.MangaSource) and \
                    not obj is mangasource.MangaSource:
                manga_sources.append(obj.__name__)
        except TypeError:
            pass

    return dict(manga_sources=manga_sources)


@app.route('/')
def home():
    return render_template('home.html')


@app.route('/site/<manga_source_name>/')
def show_site(manga_source_name):
    """displays all the manga available for a given source"""
    manga_src = getattr(mangasource, manga_source_name)()

    return render_template('manga_site.html',
                           manga_source_name=manga_source_name,
                           mangas=manga_src.get_mangas())


@app.route('/site/<manga_source_name>/update/')
def update_site(manga_source_name):
    """displays all the manga available for a given source"""
    manga_src = getattr(mangasource, manga_source_name)()
    manga_src.update_mangas()

    return redirect("/site/%s/" % manga_source_name)


if __name__ == '__main__':
    db.create_all()
    app.run(debug=True)
