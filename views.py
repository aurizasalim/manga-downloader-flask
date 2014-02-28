from flask import request, render_template

from app import app, db


@app.route('/')
def home():
    return render_template('base.html')


if __name__ == '__main__':
    app.run(debug=True)
