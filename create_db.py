from taskapp import db
from taskapp.models import User, Task

if __name__ == '__main__':
    db.create_all()