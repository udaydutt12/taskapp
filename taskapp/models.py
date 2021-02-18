from taskapp import db
from datetime import datetime

class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.String(30), primary_key=True)
    name = db.Column(db.String(50), nullable=False)
    profile_pic_url = db.Column(db.String(100), nullable=False)
    tasks = db.relationship('Task', backref='author', lazy=True)

    def __repr__(self):
        return f"({self.id}, {self.name})"

class Task(db.Model):
    __tablename__ = 'tasks'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.String(30), db.ForeignKey('users.id'),
                        nullable=False)
    title = db.Column(db.String(60), nullable=False)
    due_date = db.Column(db.Date, nullable=False)
    image_url = db.Column(db.String(50))
    status = db.Column(db.String(10), nullable=False, 
                       default="incomplete")
    content = db.Column(db.Text)
    view_order = db.Column(db.Integer, nullable=False)

    def __repr__(self):
        return f"({self.id}, {self.title}, {self.due_date},"\
                 f"{self.image_url}, {self.status})"