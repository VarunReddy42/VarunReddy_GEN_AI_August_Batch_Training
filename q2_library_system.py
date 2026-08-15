"""
Q2: Library Book Management System
------------------------------------
A small library system that picks the right data structure for each job:

- dictionary  -> catalog        (fast lookup of a book by its ID)
- tuple       -> book details   (title, author, year should not change)
- list        -> borrowed_books (keeps the order books were borrowed in)
- set         -> members        (automatically blocks duplicate member IDs)
"""


# ---------------------------------------------------------
# 1. Add a new book to the catalog
# ---------------------------------------------------------
def add_book(catalog, book_id, title, author, year):
    # Book details are stored as a tuple because once a book is added,
    # its title/author/year should not be changed by accident.
    catalog[book_id] = (title, author, year)
    print("Added:", title, "(ID:", str(book_id) + ")")


# ---------------------------------------------------------
# 2. Borrow a book
# ---------------------------------------------------------
def borrow_book(catalog, borrowed_books, book_id):
    if book_id not in catalog:
        print("Cannot borrow. Book ID", book_id, "does not exist in catalog.")
        return

    if book_id in borrowed_books:
        print("Cannot borrow. Book ID", book_id, "is already borrowed.")
        return

    borrowed_books.append(book_id)
    title = catalog[book_id][0]
    print("Borrowed:", title, "(ID:", str(book_id) + ")")


# ---------------------------------------------------------
# 3. Return a book
# ---------------------------------------------------------
def return_book(borrowed_books, book_id):
    if book_id in borrowed_books:
        borrowed_books.remove(book_id)
        print("Returned book ID:", book_id)
    else:
        print("Cannot return. Book ID", book_id, "was not borrowed.")


# ---------------------------------------------------------
# 4. Register a new member
# ---------------------------------------------------------
def register_member(members, member_id):
    # A set automatically ignores duplicates, but we still check
    # so we can print a clear message when a duplicate is attempted.
    if member_id in members:
        print("Member ID", member_id, "is already registered. Skipping.")
    else:
        members.add(member_id)
        print("Registered member ID:", member_id)


# ---------------------------------------------------------
# 5. Show available books (books not currently borrowed)
# ---------------------------------------------------------
def show_available(catalog, borrowed_books):
    print("\nAvailable Books:")
    found_any = False

    for book_id in catalog:
        if book_id not in borrowed_books:
            title, author, year = catalog[book_id]
            print("-", title, "by", author, "(" + str(year) + ")", "[ID:", str(book_id) + "]")
            found_any = True

    if not found_any:
        print("No books are currently available.")


# ---------------------------------------------------------
# Demo
# ---------------------------------------------------------
def main():
    catalog = {}          # dict: book_id -> (title, author, year)
    borrowed_books = []    # list: keeps order of borrowed book IDs
    members = set()        # set: unique member IDs

    print("--- Adding Books ---")
    add_book(catalog, 1, "The Alchemist", "Paulo Coelho", 1988)
    add_book(catalog, 2, "Atomic Habits", "James Clear", 2018)
    add_book(catalog, 3, "Deep Work", "Cal Newport", 2016)
    add_book(catalog, 4, "Clean Code", "Robert C. Martin", 2008)

    print("\n--- Registering Members ---")
    register_member(members, 101)
    register_member(members, 102)
    register_member(members, 103)
    register_member(members, 101)  # duplicate, should be ignored

    print("\n--- Borrowing Books ---")
    borrow_book(catalog, borrowed_books, 1)
    borrow_book(catalog, borrowed_books, 3)

    print("\n--- Returning a Book ---")
    return_book(borrowed_books, 1)

    show_available(catalog, borrowed_books)


if __name__ == "__main__":
    main()
