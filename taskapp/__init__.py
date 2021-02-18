from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from os import getenv

app = Flask(__name__)
app.config['SECRET_KEY'] = getenv("SECRET_KEY")
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

if getenv("PRODUCTION"):
    server = getenv('MYSQL_SERVER')
    username = getenv('MYSQL_USERNAME')
    password = getenv('MYSQL_PASSWORD')
    dbname = getenv('MYSQL_DBNAME')
    uri = f"mysql://{username}:{password}@{server}/{dbname}"
    app.config['SQLALCHEMY_DATABASE_URI'] = uri
else:
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///db.sqlite3'

db = SQLAlchemy(app)

from taskapp import routes
