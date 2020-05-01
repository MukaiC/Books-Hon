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
                    review_id INTEGER REFERENCES reviews
                    )"""



def main():
    tables = [books, reviews, users]
    for table in tables:
        engine.execute(table)
    print("tables created")

if __name__ == '__main__':
    main()
