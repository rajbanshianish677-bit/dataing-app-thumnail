from flask import Flask, request, redirect, session, send_from_directory, render_template_string
import sqlite3
import os

app = Flask(__name__)
app.secret_key = "secret123"

UPLOAD_FOLDER = "uploads"
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

if not os.path.exists("uploads"):
    os.makedirs("uploads")


def connect():
    return sqlite3.connect("database.db")


def init_db():

    conn = connect()
    cur = conn.cursor()

    cur.execute("""
    CREATE TABLE IF NOT EXISTS users(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT,
    password TEXT,
    bio TEXT,
    image TEXT
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS messages(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    sender INTEGER,
    receiver INTEGER,
    text TEXT
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS likes(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    sender INTEGER,
    receiver INTEGER
    )
    """)

    conn.commit()
    conn.close()


init_db()


login_page = '''

<style>

body{
font-family:Arial;
background:#f0f2f5;
text-align:center;
}

input,textarea{
padding:8px;
margin:5px;
width:200px;
}

button{
background:#ff4d6d;
color:white;
border:none;
padding:8px;
cursor:pointer;
}

.card{
background:white;
width:250px;
padding:10px;
margin:15px;
border-radius:10px;
box-shadow:0 0 10px rgba(0,0,0,0.2);
display:inline-block;
}

</style>

<h2>Login</h2>

<form method="POST" action="/login">

<input name="username" placeholder="Username"><br>

<input type="password" name="password" placeholder="Password"><br>

<button>Login</button>

</form>

<br>

<a href="/signup">Create Account</a>

'''


signup_page = '''

<h2>Create Account</h2>

<form method="POST" enctype="multipart/form-data">

<input name="username" placeholder="Username"><br>

<input type="password" name="password" placeholder="Password"><br>

<textarea name="bio" placeholder="Your bio"></textarea><br>

<input type="file" name="image"><br>

<button>Create</button>

</form>

<a href="/">Back</a>

'''


@app.route("/")
def home():

    if "user" in session:
        return redirect("/browse")

    return render_template_string(login_page)



@app.route("/login", methods=["POST"])
def login():

    username = request.form["username"]
    password = request.form["password"]

    conn = connect()
    cur = conn.cursor()

    user = cur.execute(
    "SELECT * FROM users WHERE username=? AND password=?",
    (username,password)
    ).fetchone()

    conn.close()

    if user:

        session["user"] = user[0]

        return redirect("/browse")

    return "Login Failed"



@app.route("/signup", methods=["GET","POST"])
def signup():

    if request.method == "POST":

        username = request.form["username"]
        password = request.form["password"]
        bio = request.form["bio"]

        image = request.files["image"]

        filename = image.filename

        image.save(os.path.join(app.config["UPLOAD_FOLDER"], filename))

        conn = connect()
        cur = conn.cursor()

        cur.execute(
        "INSERT INTO users(username,password,bio,image) VALUES(?,?,?,?)",
        (username,password,bio,filename)
        )

        conn.commit()
        conn.close()

        return redirect("/")

    return render_template_string(signup_page)



@app.route("/browse")
def browse():

    if "user" not in session:
        return redirect("/")

    conn = connect()
    cur = conn.cursor()

    users = cur.execute(
    "SELECT * FROM users WHERE id != ?",
    (session["user"],)
    ).fetchall()

    conn.close()

    html = "<h1>Browse Friends</h1>"
    html += '<a href="/logout">Logout</a><hr>'

    for u in users:

        html += f'''

        <div class="card">

        <img src="/uploads/{u[4]}" width="200"><br>

        <b>{u[1]}</b><br>

        {u[3]}<br><br>

        <a href="/like/{u[0]}">❤️ Like</a><br><br>

        <a href="/chat/{u[0]}">💬 Chat</a>

        </div>

        '''

    return html



@app.route("/like/<int:user_id>")
def like(user_id):

    conn = connect()
    cur = conn.cursor()

    cur.execute(
    "INSERT INTO likes(sender,receiver) VALUES(?,?)",
    (session["user"],user_id)
    )

    conn.commit()
    conn.close()

    return redirect("/browse")



@app.route("/chat/<int:user_id>",methods=["GET","POST"])
def chat(user_id):

    sender = session["user"]

    conn = connect()
    cur = conn.cursor()

    if request.method == "POST":

        text = request.form["text"]

        cur.execute(
        "INSERT INTO messages(sender,receiver,text) VALUES(?,?,?)",
        (sender,user_id,text)
        )

        conn.commit()

    messages = cur.execute(
    "SELECT * FROM messages WHERE (sender=? AND receiver=?) OR (sender=? AND receiver=?)",
    (sender,user_id,user_id,sender)
    ).fetchall()

    conn.close()

    html = "<h2>Chat</h2>"

    for m in messages:

        html += f"<p>{m[3]}</p>"

    html += f'''

    <form method="POST">

    <input name="text">

    <button>Send</button>

    </form>

    <br>

    <a href="/browse">Back</a>

    '''

    return html



@app.route("/uploads/<filename>")
def uploaded_file(filename):

    return send_from_directory(app.config["UPLOAD_FOLDER"],filename)



@app.route("/logout")
def logout():

    session.clear()

    return redirect("/")



app.run(host="0.0.0.0",port=5000,debug=True)