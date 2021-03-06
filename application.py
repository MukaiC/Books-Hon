import os
import requests
from flask import Flask, session, render_template, request, redirect, url_for, flash, jsonify
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
app.config["SECRET_KEY"] = os.getenv("SECRET_KEY")
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
    if 'logged_in' in session:
        flash (f'You are already logged in as {session["username"]}!', 'success')
        return redirect(url_for('search'))
    # Get form information
    if request.method=='POST':
        username = request.form.get("username")
        password = request.form.get("password")
        # Check if the user is registered
        user = db.execute("SELECT * FROM users WHERE username = :username", {"username": username}).fetchone()
        # Validate the user
        if user is not None and bcrypt.check_password_hash(user.password, password):
            session["user_id"] = user.id
            session["username"] = username
            session["logged_in"] = True
            flash(f'You are now logged in as {session["username"]}!', 'success')
            return redirect(url_for('search'))
        # If not validated
        else:
            flash('Login Unsuccessful. Please check username and password', 'danger')

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
            # Make sure the username does not already exist
            existing_username = db.execute("SELECT * FROM users WHERE username = :username", {"username": username}).fetchone()
            if existing_username is not None:
                return render_template ("error.html", message="That username is taken. Please choose a different one.", title="Error", link="register")
            # Make sure the email does not already exist
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


@app.route("/logout")
def logout():
    session.pop('user_id', None)
    session.pop('username', None)
    session.pop('logged_in', None)
    flash('You are now logged out', 'success')
    return redirect(url_for('index'))

@app.route("/error")
def error():
    message = request.args.get('message')
    link = request.args.get('link')
    title = request.args.get('title')
    return render_template("error.html", message=message, link=link, title=title)

@app.route("/search", methods=["GET", "POST"])
def search():
    if 'logged_in' not in session:
        flash('Please log in first', 'danger')
        return redirect(url_for('login'))
    # Get form information, remove whitespace at beginning and ending
    if request.method=='POST':
        title = request.form.get("title").title()
        author = request.form.get("author").title()
        isbn = request.form.get("isbn")
        # Make sure at least one field is filled
        if title == '' and author == '' and isbn == '':
            flash('Please enter title, author or ISBN number', 'danger')

        else:
            # Search the database for matching books
            books = db.execute("SELECT * FROM books WHERE title LIKE :title AND author LIKE :author AND isbn LIKE :isbn", {"title": f"%{title}%", "author": f"%{author}%", "isbn": f"%{isbn}%"}).fetchall()
            book_count=len(books)
            if book_count != 0:
                return render_template("books.html", books=books, book_count=book_count)
            else:
                flash('0 matching books found', 'danger')

    return render_template("search.html")


@app.route("/search/<int:book_id>", methods=["GET", "POST"])
def book(book_id):
    """Lists details about a book and reviews if any"""
    # Make sure the book exists
    book = db.execute("SELECT * FROM books WHERE id = :id", {"id": book_id}).fetchone()
    if book is None:
        return redirect (url_for('error', message="No such book", link="search"))

    # Get the avarage rating and number of ratings from goodreads
    res = requests.get("https://www.goodreads.com/book/review_counts.json", params={"key":os.getenv("GOODREADS_API_KEY"), "isbns":book.isbn})
    if res.status_code != 200:
        raise Exception ("Error: API request unsuccessful.")
    data = res.json()
    gr_average_rating = data['books'][0]['average_rating']
    gr_work_ratings_count = data ['books'][0]['work_ratings_count']

    # Get reviews from users if any
    user_count = 0
    user_rating = None

    # Get reviews for this book
    reviews = db.execute("SELECT * FROM reviews WHERE book_id = :book_id", {"book_id": book_id}).fetchall()
    # Count the number of existing reviews
    reviews_count = len(reviews)
    reviewed_users = []
    if reviews_count != 0:
        user_count = reviews_count
        # Create list of users who have rated this book
        for review in reviews:
            reviewed_users.append(review.user_id)
        # Get average rating
        avg_user_rating = db.execute("SELECT AVG(rating) FROM reviews WHERE book_id = :book_id", {"book_id": book_id}).fetchone()
        user_rating = round(avg_user_rating[0],2)
    # If a review is submitted
    if request.method == 'POST':
        rating = request.form.get('rating')
        review = request.form.get('review')
        if rating is not None:
            db.execute("INSERT INTO reviews (rating, comment, book_id, user_id) VALUES (:rating, :comment, :book_id, :user_id)", {"rating": rating, "comment": review, "book_id": book_id, "user_id": session["user_id"]})

            db.commit()
            flash('Thank you for rating!', 'success')
            return redirect(url_for('book', book_id=book_id))
        else:
            flash('Please enter your rating', 'danger')

    return render_template("book.html", book=book, gr_rating=gr_average_rating, gr_count=gr_work_ratings_count, user_count=user_count, user_rating=user_rating, reviews=reviews, reviewed_users=reviewed_users)

@app.route("/api/<isbn>")
def book_api(isbn):
    # Make sure book exists.
    book = db.execute("SELECT * FROM books WHERE isbn = :isbn", {"isbn": isbn}).fetchone()
    if book is None:
        return jsonify({"error": "Book not found"}), 404

    # Get all ratings.
    ratings = db.execute("SELECT rating FROM reviews WHERE book_id = :book_id", {"book_id": book.id}).fetchall()
    ratings_count = len(ratings)

    if ratings_count != 0:
        ratings_total = 0
        for rating in ratings:
            ratings_total += rating[0]
            average_score = round((ratings_total / ratings_count), 2)
    else:
        average_score = None

    return jsonify({
        "title": book.title,
        "author": book.author,
        "year": book.year,
        "isbn": book.isbn,
        "review_count": ratings_count,
        "average_score": average_score
    })

if __name__ == "__main__":
    app.run(debug=True)
