import os
from sqlalchemy import create_engine

# Check for environment variable
if not os.getenv("DATABASE_URL"):
    raise RuntimeError("DATABASE_URL is not set")

engine = create_engine(os.getenv("DATABASE_URL"))


# Command to create books table
books = """ CREATE TABLE IF NOT EXISTS books(
                    id SERIAL PRIMARY KEY,
                    isbn VARCHAR NOT NULL,
                    title VARCHAR NOT NULL,
                    author VARCHAR NOT NULL,
                    year INTEGER NOT NULL
                    )"""
# Command to create reviews table
reviews = """ CREATE TABLE IF NOT EXISTS reviews(
                    id SERIAL PRIMARY KEY,
                    rating INTEGER NOT NULL,
                    comment VARCHAR,
                    book_id INTEGER REFERENCES books
                    )"""

# Command to create users table
users = """ CREATE TABLE IF NOT EXISTS users(
                    id SERIAL PRIMARY KEY,
                    username VARCHAR NOT NULL,
                    email VARCHAR NOT NULL,
                    password VARCHAR NOT NULL,
                    review_id INTEGER REFERENCES reviews
                    )"""

# Command to add user_id column to review tables
add_user_id = """ ALTER TABLE reviews ADD COLUMN IF NOT EXISTS user_id INTEGER REFERENCES users """

# Command to delete review_id in users tables
drop_review_id = """ ALTER TABLE users DROP COLUMN IF EXISTS review_id """


def main():
    tables = [books, reviews, users]
    for table in tables:
        engine.execute(table)
    print("tables created")

    engine.execute(add_user_id)
    print ("user_id is added to reviews table")

    engine.execute(drop_review_id)
    print ("review_id is removed from users table")


if __name__ == '__main__':
    main()
