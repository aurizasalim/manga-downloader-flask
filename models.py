from sqlalchemy import types
from sqlalchemy.ext.compiler import compiles
from sqlalchemy.dialects import postgres

from app import db
from constants import QUEST_ITEMS, GEMS
from utils import norm, normfind


"""
using tsvectors for full text search in sqlalchemy, custom type definition

http://stackoverflow.com/questions/13837111/
"""


class tsvector(types.TypeDecorator):
    impl = types.UnicodeText


@compiles(tsvector, 'postgresql')
def compile_tsvector(element, compiler, **kw):
    return 'tsvector'

# def is_gem(query):
#     return query.join(Item.requirements).filter(
#         Item.properties.any(name="Experience")
#     )

# def is_quest_item(query):
#     return query.filter(func.lower(Item.type).in_(QUEST_ITEMS))


def get_chromatic_stash_pages():
    """returns all the stash pages that are chromatic"""
    premium_pages = Location.query.filter(
        Location.is_premium,
        Location.is_character == False,
    ).all()
    for i, p in enumerate(premium_pages):
        if p.name.lower().startswith("chromatic"):
            return range(premium_pages[i].page_no,
                         premium_pages[i + 1].page_no)


def get_rare_stash_pages():
    """returns all the stash pages that are rare"""
    premium_pages = Location.query.filter(
        Location.is_premium,
        Location.is_character == False,
    ).all()

    #longest non premium range are the rares
    diffs = []
    for i, p in enumerate(premium_pages[:-1]):
        curr = premium_pages[i].page_no
        nxt = premium_pages[i + 1].page_no
        diffs.append((nxt - (curr + 1), range(curr + 1, nxt)))
    return max(diffs)[-1]


class Item(db.Model):
    """
    Model representing an item
    """
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255))
    type = db.Column(db.String(255), nullable=False)
    #x, y can be null for equipped or socketed items
    x = db.Column(db.SmallInteger())
    y = db.Column(db.SmallInteger())
    w = db.Column(db.SmallInteger(), nullable=False, default=1)
    h = db.Column(db.SmallInteger(), nullable=False, default=1)
    rarity = db.Column(db.Enum('normal', 'magic', 'rare', 'unique',
                                name='rarities'))
    num_sockets = db.Column(db.SmallInteger(), nullable=False, default=0)
    socket_str = db.Column(db.String(20), nullable=False, default="")
    is_identified = db.Column(db.Boolean, nullable=False, default=True)
    char_location = db.Column(db.String(20))
    full_text = db.Column(tsvector, nullable=False)

    #funky stuff for item properties, mods etc
    mods = db.Column(postgres.ARRAY(db.String(255)))
    requirements = db.relationship("Requirement", backref="item")
    properties = db.relationship("Property", backref="item")
    location_id = db.Column(db.Integer, db.ForeignKey('location.id'))

    #socketed items use these for the parent item
    parent_id = db.Column(db.Integer, db.ForeignKey('item.id'))
    parent_item = db.relationship('Item', remote_side=[id],
                                  backref="socketed_items")

    def __repr__(self):
        return self.name + self.type

    @db.validates('num_sockets')
    def validate_num_sockets(self, key, num_sockets):
        assert 0 <= num_sockets <= 6, num_sockets
        return num_sockets

    @db.validates('x')
    def validate_x(self, key, x):
        assert (0 <= x <= 11) or x is None, x
        return x

    @db.validates('y')
    def validate_y(self, key, y):
        assert (0 <= y <= 11) or y is None, y
        return y

    @db.validates('w')
    def validate_w(self, key, w):
        assert 1 <= w <= 2, w
        return w

    @db.validates('h')
    def validate_h(self, key, h):
        assert 1 <= h <= 4, h
        return h

    #various helpers for the model
    def is_gem(self):
        for p in self.properties:
            if p.name == "Experience":
                return True
        return False

    def is_quest_item(self):
        return norm(self.type).startswith(QUEST_ITEMS)

    @property
    def identified(self):
        return self.query.filter(self.is_identified)

    def location_str(self):
        """Outputs a nicely formatted location string"""
        ret = "%s: " % str(self.location)
        if self.char_location:
            ret += self.char_location
        elif self.x is not None:
            ret += "(%s, %s)" % (self.x, self.y)
        if self.parent_item:
            ret += " [Socketed]"
        return ret

    def gem_color(self):
        """
        returns the letter for the color of the gem, if the item is not a gem,
        raises ValueError
        """
        for p in self.properties:
            if p.name == "Experience":
                break
        else:
            raise ValueError("Item is not a gem.")
        return normfind(GEMS, self.type)["color"]


class Property(db.Model):
    """
    Model representing a single property of an item
    """
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    value = db.Column(db.String(255))
    item_id = db.Column(db.Integer, db.ForeignKey('item.id'))


class Requirement(db.Model):
    """
    Model representing a single requirement of an item
    """
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    value = db.Column(db.SmallInteger(), nullable=False)
    item_id = db.Column(db.Integer, db.ForeignKey('item.id'))


class Location(db.Model):
    """
    Model representing the location of an item, which might be a stash page
    or a character
    """
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    page_no = db.Column(db.SmallInteger())
    is_premium = db.Column(db.Boolean, nullable=False, default=False)
    is_character = db.Column(db.Boolean, nullable=False, default=False)
    items = db.relationship("Item", backref="location")

    def __str__(self):
        if self.is_character:
            return self.name
        return "Stash: %s" % self.name

    def __repr__(self):
        return self.__str__()
