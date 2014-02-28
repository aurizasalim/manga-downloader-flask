from flask import Flask
from flask.ext.sqlalchemy import SQLAlchemy

app = Flask(__name__, static_path='/static')
DATABASE_URL = 'postgresql://postgres:password@localhost:5432/manga'
app.config['SQLALCHEMY_DATABASE_URI'] = DATABASE_URL

#custom session so we can have django manager like functionality
db = SQLAlchemy(app)
