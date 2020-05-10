import os

from flask import Flask, session, render_template, request, redirect, url_for, flash
from flask_session import Session
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker
from flask_bcrypt import Bcrypt

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

bcrypt = Bcrypt(app)

@app.route ("/")
@app.route ("/index")
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
    # When it is coming from registration form
    if request.method=='POST':
        username = request.form.get("username")
        email = request.form.get("email")
        password = request.form.get("password")
        confirm_password = request.form.get("confirm_password")

    # Make sure form information is valid
        if username=='':
            return render_template ("error.html", message="Invalid username", title="Error", link="register")
        elif email=='':
            return render_template ("error.html", message="Invalid Email adress", title="Error", link="register")
        elif password=='' or password != confirm_password:
            flash('Please enter a matching password to confirm', 'danger')


        else:
            # make sure the username does not already exist
            existing_username = db.execute("SELECT * FROM users WHERE username = :username", {"username": username}).fetchone()
            if existing_username is not None:
                return render_template ("error.html", message="That username is taken. Please choose a different one.", title="Error", link="register")
            # make sure the email does not already exist
            existing_email = db.execute("SELECT * FROM users WHERE email = :email", {"email": email}).fetchone()
            if existing_email is not None:
                return render_template ("error.html", message="That email is taken. Please choose a different one.", title="Error", link="register")

            else:
                hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')
                db.execute("INSERT INTO users (username, email, password) VALUES (:username, :email, :hashed_password)", {"username": username, "email": email, "hashed_password": hashed_password})
                db.commit()
                flash('Your account has been created! You are now able to log in', 'success')
                return redirect (url_for('login'))

    return render_template("register.html")


# @app.route("/error")
# def error():
#     return render_template("error.html")

@app.route("/search")
def search():
    return render_template("search.html")

if __name__ == "__main__":
    app.run(debug=True)
