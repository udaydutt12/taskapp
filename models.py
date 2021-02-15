from flask import Flask
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///book.sqlite'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

class User(db.Model):
    pass

class ToDO(db.Model):
    pass


class User(db.Model):
    __tablename__ = 'users'
    usr_id = db.Column(UUID(as_uuid=True), primary_key=True, server_default=text("uuid_generate_v4()"))
    usr_name = db.Column(db.String, nullable=False)
    usr_email = db.Column(db.String, nullable=False)
    usr_pass =  db.Column(db.String, nullable=False)

