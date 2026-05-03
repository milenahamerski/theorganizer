from fastapi import APIRouter, HTTPException
from typing import List
from .models import Book
from .database import get_connection

router = APIRouter()


@router.post("/books", response_model=Book)
def create_book(book: Book):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute(
        "INSERT INTO books (title, author, year, image_url) VALUES (%s, %s, %s, %s)",
        (book.title, book.author, book.year, book.image_url)
    )

    conn.commit()
    book.id = cur.lastrowid

    cur.close()
    conn.close()

    return book


@router.get("/books", response_model=List[Book])
def list_books():
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("SELECT id, title, author, year, image_url FROM books")
    rows = cur.fetchall()

    cur.close()
    conn.close()

    return [
        Book(id=r[0], title=r[1], author=r[2], year=r[3], image_url=r[4])
        for r in rows
    ]


@router.get("/books/{book_id}", response_model=Book)
def get_book(book_id: int):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute(
        "SELECT id, title, author, year, image_url FROM books WHERE id = %s",
        (book_id,)
    )

    row = cur.fetchone()

    cur.close()
    conn.close()

    if not row:
        raise HTTPException(status_code=404, detail="Book not found")

    return Book(id=row[0], title=row[1], author=row[2], year=row[3], image_url=row[4])


@router.put("/books/{book_id}", response_model=Book)
def update_book(book_id: int, book: Book):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute(
        """
        UPDATE books
        SET title=%s, author=%s, year=%s, image_url=%s
        WHERE id=%s
        """,
        (book.title, book.author, book.year, book.image_url, book_id)
    )

    conn.commit()

    if cur.rowcount == 0:
        raise HTTPException(status_code=404, detail="Book not found")

    cur.close()
    conn.close()

    book.id = book_id
    return book


@router.delete("/books/{book_id}")
def delete_book(book_id: int):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("DELETE FROM books WHERE id = %s", (book_id,))
    conn.commit()

    if cur.rowcount == 0:
        raise HTTPException(status_code=404, detail="Book not found")

    cur.close()
    conn.close()

    return {"message": "Book deleted successfully"}
