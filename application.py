import os

from flask import Flask, session, render_template, request, redirect, url_for
from flask_session import Session
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker

app = Flask(__name__)

# Check for environment variable
if not os.getenv("DATABASE_URL"):
    raise RuntimeError("DATABASE_URL is not set")

# Configure session to use filesystem
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Set up database
engine = create_engine(os.getenv("DATABASE_URL"))
db = scoped_session(sessionmaker(bind=engine))


@app.route("/")
@app.route("/home")
def index():
    return render_template("index.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    # !Get form information
    if request.method=='POST':
        username = request.form.get("username")
        return redirect(url_for('search'))

    return render_template("login.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    # !Get form information
    if request.method=='POST':
        username = request.form.get("username")
        if username=='':
            return render_template ("error.html", message="Invalid username", title="Error")
        return redirect (url_for('login'))
    # !Make sure form information is Invalid

    # !store the registration data in the database

    return render_template("register.html")

@app.route("/search")
def search():
    return render_template("search.html")

if __name__ == "__main__":
    app.run(debug=True)
