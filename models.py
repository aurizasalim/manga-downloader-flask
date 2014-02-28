from app import db
from datetime import date


class Manga(db.Model):
    """
    Model representing a single requirement of an item
    """
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    link = db.Column(db.Text(), nullable=False)
    fav = db.Column(db.Boolean, nullable=False, default=False)
    mangasite = db.Column(db.String(20), nullable=False)
    last_updated = db.Column(db.Date, nullable=True, onupdate=date.today)

    def __repr__(self):
        return "(%s) %s" % (self.mangasite, self.name)
