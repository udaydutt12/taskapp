from flask import (flash, redirect,render_template, 
                   request, session, abort)
from taskapp import app, db
from taskapp.models import User, Task
from taskapp.forms import TaskForm
from taskapp.helpers import login_required, upload_s3
import requests
from os import getenv

GOOGLE_CLIENT_ID = getenv('GOOGLE_CLIENT_ID')
GOOGLE_CLIENT_SECRET = getenv('GOOGLE_CLIENT_SECRET')
redirect_uri = getenv('REDIRECT_URI')

@app.route("/orderupdate",methods=["POST"])
@login_required
def orderupdate():  
    user = User.query.get(session["user_id"])
    tasks = user.tasks
    n = len(tasks)
    order = request.form['order'].split(",", n)
    for i, task_id in enumerate(order):
        task = Task.query.get(int(task_id))
        task.view_order = i
    db.session.commit()
    return redirect("/")
    
@app.route("/update/<task_id>", methods = ["GET", "POST"])
@login_required
def update_task(task_id):
    task = Task.query.get(task_id)
    if task.author.id != session["user_id"]:
        return "You can't update this task,"\
               "as you are not the Author."
    form = TaskForm()
    if form.validate_on_submit():
        image_url = task.image_url
        if request.files["image"]:
            image_url = upload_s3(request)
        task.title = form.title.data
        task.content = form.content.data
        task.image_url = image_url
        task.status = form.status.data
        task.due_date = form.due_date.data
        db.session.commit()
        flash("You have successfully edited this Task!", "success")
        return redirect(f"/n/{task_id}")    
    elif request.method == "GET":
        form.title.data = task.title
        form.content.data = task.content
        form.status.data = task.status
        form.due_date.data = task.due_date
    return render_template("new.html", form=form, title="Update Task",
                           action=f"/update/{task_id}")


@app.route("/new", methods=["GET", "POST"])
@login_required
def new():
    form = TaskForm()
    if form.validate_on_submit():
        if form.status.data == "Incomplete":
            n = len(Task.query.filter_by(user_id=session["user_id"],
                    status="Incomplete").all())
        else:
            n = len(User.query.get(session["user_id"]).tasks)
        image_url = None
        if request.files['image']:
            image_url = upload_s3(request)
        task = Task(title=form.title.data, content=form.content.data,
                    due_date=form.due_date.data, 
                    image_url=image_url, status=form.status.data, 
                    view_order=n + 1, author=User.query.get(session["user_id"]))
        db.session.add(task)
        db.session.commit()
        flash('Your task has been published!', 'success')
        return redirect(f"/n/{task.id}") 
    return render_template("new.html", title="New Task",form=form)

@app.route("/n/<task_id>")
@login_required
def view_task(task_id):
    task = Task.query.get(task_id)
    if task:
        return render_template("task.html", task=task)
    abort(404)

@app.route("/")
def index():
    if session.get("user_id"):
        #page = request.args.get("page", 1, type=int)
        tasks = Task.query.filter_by(user_id=session.get("user_id"))\
                                     .order_by(Task.view_order)
        incomplete_tasks, complete_tasks = [], []
        for task in tasks:
            if task.status == "Complete":
                complete_tasks.append(task)
            else:
                incomplete_tasks.append(task)
        return render_template("index.html", 
                               incomplete_tasks=incomplete_tasks,
                               complete_tasks=complete_tasks)
    return render_template("signin.html")

@app.route("/login")
def login():
    if request.args.get("next"):
        session["next"] = request.args.get("next")
    google_redirect = f"https://accounts.google.com/o/oauth2/v2/auth?scope"\
                      f"=https://www.googleapis.com/auth/userinfo.profile"\
                      f"&access_type=offline&include_granted_scopes=true"\
                      f"&response_type=code&redirect_uri={redirect_uri}"\
                      f"&client_id={GOOGLE_CLIENT_ID}"
    return redirect(google_redirect)

@app.route("/authorized")
def authorized():
    r = requests.post("https://oauth2.googleapis.com/token", 
                      data={ "client_id": GOOGLE_CLIENT_ID,
                             "client_secret": GOOGLE_CLIENT_SECRET,
                             "code":  request.args.get("code"),
                             "grant_type": "authorization_code",
                             "redirect_uri": redirect_uri})
    access_token = r.json()["access_token"]
    response = requests.get(f"https://www.googleapis.com/oauth2/v2/userinfo"\
                            f"?access_token={access_token}").json()
    user = User.query.get(response["id"])
    if user:
        session["user_id"] = user.id
        session["name"] = user.name
        session["avatar"] = user.profile_pic_url
    else:
        from sqlalchemy import create_engine
        from sqlalchemy.orm import scoped_session, sessionmaker
        engine = create_engine(app.config['SQLALCHEMY_DATABASE_URI'])
        db2 = scoped_session(sessionmaker(bind=engine))
        conn = db2()
        c = conn
        mapping = {"id": response["id"], 
                   "name": response["name"],
                   "photo": response["picture"]}
        c.execute("Insert Into users (id, name, profile_pic_url)"\
                  "VALUES (:id, :name, :photo)",
                  mapping)
        conn.commit()
        session["user_id"] = response["id"]
        session["name"] = response["name"]
        session["avatar"] = response["picture"]
    if session.get("next"):
        return redirect(session.get("next"))
    return redirect("/")


@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")

@app.route("/delete")
@login_required
def delete_task():
    task = Task.query.get(request.args.get("n"))
    if task and task.author.id == session["user_id"]:
        db.session.delete(task)
        db.session.commit()
        flash("You have successfully deleted this task!", "success")
        return redirect("/")
    return "You do not have permission to modify this task."
