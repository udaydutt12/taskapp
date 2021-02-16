from flask import jsonify, Flask, redirect, url_for, render_template, request, session, abort
#from models import db
import requests
import sqlite3
from helpers import login_required, random_str, upload_s3

# Flask
app = Flask(__name__)
app.config['SECRET_KEY'] = '\x14B~^\x07\xe1\x197\xda\x18\xa6[[\x05\x03QVg\xce%\xb2<\x80\xa4\x00'
#app.config['DEBUG'] = True
conn = sqlite3.connect("db.sqlite3", check_same_thread=False)
c = conn.cursor()
# Database
#app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///book.sqlite'
#app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
#app.config['DEBUG'] = True
#db.init_app(app)

# db.create_all()
def validate_task(user_id, task_id):
    _ = c.execute("Select * from tasks where user_id=:user_id and task_id=:task_id", {"user_id": user_id, "task_id": task_id}).fetchall()
    if len(_) == 0:
        return False
    return True

@app.route("/new", methods=["GET", "POST"])
@login_required
def new():
    if request.method == "POST":
        url = upload_s3(request)
        code = random_str()
        while True:
            row = c.execute("Select * From tasks Where task_id=:id", {"id": code}).fetchall()
            if not row:
                break
            code = random_str()
        c.execute("Insert Into tasks (content, severity, image, title, description, task_id, user_id) Values (:content, :severity, :image, :title, :desc, :tid, :uid)", 
                   {"content": request.form.get('content'), "severity": request.form.get('severity'), "image": url, "title": request.form.get("title"), "desc": request.form.get("description"), "tid": code, "uid": session.get("user_id")}) 
        conn.commit()
        return redirect(f"/n/{code}")
    else:
        return render_template("newTask.html", action="/new")
    
@app.route("/login")
def login():
    if request.args.get("next"):
        session["next"] = request.args.get("next")
    return redirect(f"https://accounts.google.com/o/oauth2/v2/auth?scope=https://www.googleapis.com/auth/userinfo.profile&access_type=offline&include_granted_scopes=true&response_type=code&redirect_uri=http://127.0.0.1:5000/authorized&client_id={GOOGLE_CLIENT_ID}")

@app.route("/authorized")
def authorized():
    r = requests.post("https://oauth2.googleapis.com/token", data={
        "client_id": GOOGLE_CLIENT_ID,
        "client_secret": GOOGLE_CLIENT_SECRET,
        "code":  request.args.get("code"),
        "grant_type": "authorization_code",
        "redirect_uri": "http://127.0.0.1:5000/authorized"
    })
    access_token = r.json()["access_token"]
    r = requests.get(f"https://www.googleapis.com/oauth2/v2/userinfo?access_token={access_token}").json()
    user = c.execute("Select * from users where id=:id", {"id": r["id"]}).fetchall()
    if len(user) != 0:
        session["user_id"] = user[0][0]
        session["name"] = user[0][1]
        session["avatar"] = user[0][2]
    else:
        c.execute("INSERT INTO users (id, name, photo) VALUES (:id, :name, :photo)", {"id": r["id"], "name": r["name"], "photo": r["picture"]})
        conn.commit()
        session["user_id"] = r["username"]
        session["name"] = r["name"]
        session["avatar"] = r["picture"]
    if session.get("next"):
        return redirect(session.get("next"))
    return redirect("/")

@app.route("/")
def index():
    if session.get("user_id"):
        tasks = c.execute("Select * From tasks Where user_id=:user_id", {"user_id": session.get("user_id")}).fetchall()
        return render_template("index.html", tasks=tasks)
    return render_template("signin.html")


@app.route("/home")
@login_required
def home():
    tasks = c.execute("Select * from tasks where user_id=:user_id", {"user_id": session.get("user_id")}).fetchall()
    return render_template("index.html", tasks=tasks)

@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")

@app.route("/aws", methods=["GET", "POST"])
def aws():
    if request.method == "POST":
        upload_s3(request)
        return ""
    else:
        return "<form method='POST' enctype='multipart/form-data'><input type='file' name='image'><input type='submit'></form>"

@app.route("/n/<task_id>")
@login_required
def view_task(task_id):
    '''task = c.execute("Select * From tasks WHere task_id=:task_id and user_id=:user_id",
                    {"task_id": task_id, "user_id": session.get("user_id")}).fetchall()
    if len(task) == 1:
        print("1", task)
        return render_template("task.html", task=task[0])'''
    task = c.execute("Select * From tasks Where task_id=:task_id",
                    {"task_id": task_id}).fetchall()
    if len(task) == 1:
        return render_template("task.html", task=task[0])
    abort(404)

@app.route("/a/<user_id>")
def view_author(user_id):
    # notes = c.execute("Select * From tasks Where user_id=:id and severity='2'", {'id': user_id}).fetchall()
    tasks = c.execute("Select * From tasks Where user_id=:id", {'id': user_id}).fetchall()
    return render_template("author.html", tasks= tasks)

# todo
@app.route("/update/<task_id>", methods = ["GET", "POST"])
def update_task(task_id):
    if validate_task(session.get("user_id"), task_id):
        if request.method == "POST":
            if not request.files["image"]:
                img = c.execute("select image from tasks where task_id=:id", {"id": task_id}).fetchall()[0][0]
            else:
                img = upload_s3(request)
            c.execute("Update tasks Set title=:title, description=:desc, severity=:severity, content=:content, image=:image Where task_id=:tid",
                      {"title": request.form.get("title"), "content": request.form.get("content"), "severity": request.form.get("severity"),
                       "desc": request.form.get("desc"), "image": img, "tid": task_id})
            conn.commit()
            return redirect(f"/n/{task_id}")    
        else:
            task = c.execute("Select * From tasks where task_id=:id", {"id": task_id}).fetchall()
            return render_template("newTask.html", title=task[0][2], desc=task[0][3], severity=task[0][5], content=task[0][6], image=task[0][4], action=f"/update/{task_id}")
    return "You can't update this task"

@app.route("/search")
def search():
    if request.args.get("q"):
        # results = c.execute(f"SELECT * FROM tasks WHERE title LIKE '%{request.args.get('q')}%' AND severity='2'").fetchall()
        results = c.execute(f"SELECT * FROM tasks WHERE title LIKE '%{request.args.get('q')}%'").fetchall() 
        data = []
        for result in results:
            name = c.execute("SELECT name FROM users WHERE id=:id", {"id": result[1]}).fetchall()[0][0]
            #data.append([result[4], result[5], result[6], result[0], result[1], name])
            data.append((result[2], result[3], result[4], name, result[1], result[0]))
        return render_template("searched.html", data=data)

'''results = c.execute(f"SELECT * FROM tasks WHERE title LIKE '%{request.args.get('s')}%' AND status='Public'").fetchall()
    print(results)
    data = []
    for result in results:
        name = c.execute("SELECT name FROM users WHERE user_id=:id", {"id": result[1]}).fetchall()[0][0]
        data.append([result[4], result[5], result[6], result[0], result[1], name])
    return render_template("searched.html", data=data)'''

@app.route("/delete")
def delete_task():
    if validate_task(session.get("user_id"), request.args.get("n")):
        c.execute("Delete From tasks where task_id=:tid", {"tid": request.args.get("n")})
        conn.commit()
        return redirect("/")
    return "You do not have permission to modify this task."

if __name__ == "__main__":
    app.run(port=5000)
