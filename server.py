from functools import wraps
from flask import *
from flask.ext.sqlalchemy import SQLAlchemy

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:////tmp/test.db"
db = SQLAlchemy(app)

#Creates User model for the database
class User(db.Model):
        id = db.Column(db.Integer, primary_key=True)
        username = db.Column(db.String(80), unique=True)
        password = db.Column(db.String(120), unique=True)

        def __init__(self, username, password):
                self.username = username
                self.password = password

        def __repr__(self):
                return '<User %r>' % self.username  

#Creates Post model for the database
class Post(db.Model):
  id = db.Column(db.Integer, primary_key=True, unique=True)
  author = db.Column(db.String(80))
  title = db.Column(db.String(140))
  content = db.Column(db.Text())
  uploaded_date = db.Column(db.DateTime(), default=db.func.now(), onupdate=db.func.now())

  def __init__(self, title, content):
    self.author = session["username"]
    self.title = title
    self.content = content

  def __repr__(self):
    return '<Post %r>' % self.title

#Takes in username and password from POST and checks to see if it matches in the db, returns none if there's no match
def check_auth(username, password):
  if User.query.filter(User.username == username).first():
    user = User.query.filter(User.username == username).first()
    return user.password == password
  else:
    return None

#checks if username is unique, if not renders registration page
def check_username(username):
  if User.query.filter(User.username == username).first():
#count() returns an int, anything greater than zero is true so it returns true
    return User.query.filter(User.username == username).count() > 0 

#a decorator that takes in a function to see if user is in session and sends them to
#login if they're not logged in
def requires_auth(fn):
  @wraps(fn)
  def decorated(*args, **kwargs):
    if 'username' in session:
      return fn(*args, **kwargs)
    else:
      return render_template("login.html") 
  return decorated

#renders index.html at root
@app.route("/", methods=["GET"])
def index():
  return render_template("index.html", posts=Post.query.all())

#defined login method by checking POST and checks if session matches username from the form, if iit does renders post, if not renders login
@app.route("/login", methods=["GET", "POST"])
def login():
  if request.method == "POST":
    if check_auth(request.form["username"], request.form["password"]):
      session["username"] = request.form["username"]
      return redirect(url_for("index"))
    else:
      return render_template("login.html")
  return render_template("login.html")

@app.route("/register", methods=["GET", "POST"])
def register():
  if request.method == "POST":
    if check_username(request.form["username"]):
      return redirect(url_for("register"))
    else:
      new_user = User(request.form["username"], request.form["password"])
      db.session.add(new_user)
      db.session.commit()
    return render_template("login.html")
  return render_template("register.html")

#stops session by deleting username and returns to index
@app.route("/logout")
def logout():
  session.pop("username", None)
  return redirect(url_for("index"))

#routes to post.html
@app.route("/post", methods=["GET", "POST"])
@requires_auth
def post():
  if request.method == "POST":
    if request.form["submit"] == "submit_new":
      #insantiate an instance of the post class from form data
      new_post = Post(request.form["title"], request.form["content"])
      #add to dataabase
      db.session.add(new_post)
      db.session.commit()
    #deletes if the username in session matches the author, gets id from "edit_{{ post.id }} value in delete button
    if request.form["submit"].startswith("edit_") and session["username"] == Post.query.get("author"):
      post_id = request.form["submit"].split("_")[1]
      db.session.delete(Post.query.get(post_id))
      db.session.commit()
      return render_template("post.html", posts=Post.query.all())
  return render_template("post.html", posts=Post.query.all())

#routes to a single post at /post/<id>
@app.route("/post/<id>", methods=["GET", "POST"])
def single_post(id = None):
  post = None
  if id:
    post = Post.query.get(id)
    if request.method == "POST":
        post.title = request.form["title"]
        post.content = request.form["content"]
        db.session.commit()
    print post.author
  return render_template("single_post.html", post = post)
  

@app.route("/edit/<id>", methods=["GET", "POST"])
def edit(id = None):
  post = None
  if id:
    post = Post.query.get(id)
    #if the username in session matches the author allow edit, else render post page
    if session["username"] == post.author:
      return render_template("edit.html", post = post)
    else:
      return render_template("post.html", posts=Post.query.all())

#creates secret key for session and declares host
if __name__ == "__main__":
  app.secret_key = "doashd"
  app.run(host='107.170.218.166', port=5000, debug=True)
