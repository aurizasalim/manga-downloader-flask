from flask import request, render_template

import mangasource
from app import app, db


@app.context_processor
def manga_sources():
    manga_sources = []
    for obj in mangasource.__dict__.values():
        try:
            if not obj is mangasource.MangaSource and \
                issubclass(obj, mangasource.MangaSource):
                manga_sources.append(obj.__name__)
        except TypeError:
            pass

    return dict(manga_sources=manga_sources)


@app.route('/')
def home():
    return render_template('home.html')


@app.route('/browse/<manga_source_name>/')
def browse(manga_source_name):
    """displays all the manga available for a given source"""
    manga_src = getattr(mangasource, manga_source_name)()
    mangas = manga_src.get_manga_list()
    import q
    q(mangas)

    return render_template('manga_site.html',
                           manga_source_name=manga_source_name,
                           mangas=mangas)


if __name__ == '__main__':
    app.run(debug=True)
