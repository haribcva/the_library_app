__author__ = 'haribala'

# other choice of data struc is MultiDict used by flask
# { name: [bookInfoClass]
lend_books_db = {}

# borrowerData = [borrower_email, date_borr, date_to_return, times_borrowed]

STATUS_FREE     = 0
STATUS_BORROWED = 1

class bookDatabase(object):
    """ base class for the storage of books; it is expected that derived classes
    will be built on top of it implementing multiple approaches."""
    pass

import shelve

""" file backed pickle is the simplest way to store the database"""
class bookDatabasePickle(bookDatabase):
    def __init__(self):
        self.db = shelve.open("./books_database", flag="c")

    def store_book(self, name, blob):
        print ("store_book name is", name)
        self.db[name] = blob


class bookInfoClass:
    def __init__(self, owner_email):
        self.owner = owner_email
        self.status = STATUS_FREE
        self.borrowerData = None

dbObject = bookDatabasePickle()

import unicodedata
def add_book(name, owner_email):
    # will initialize status as free, borrower_data as None
    # normalize name, to begin with make it to all lowercaps
    if (type(name) is unicode):
        name = unicodedata.normalize('NFKD', name).encode('ascii','ignore')
    name = name.upper()
    if (name in lend_books_db):
        # book exits; make sure the same person is not adding it again
        data = lend_books_db[name]
        for each in data:
            if (each.owner == owner_email):
                ## duplicate insertion from same owner, return
                return False

        ## add it to the database
        data = bookInfoClass(owner_email)
        # lend_books_db[name].append(data)
    else:
        ## add it to the database
        data = bookInfoClass(owner_email)
        # lend_books_db[name] = [data]

    dbObject.store_book(name, data)
    return True

def remove_book():
    pass

def get_books(user=None, name=None):
    print ("get_books passed ", user, name)
    books = []
    # for book in lend_books_db:
    for book in dbObject.db:
        data = dbObject.db[book]
        if ((user is None and name is None) or (user is not None and data.owner == user) or (name is not None and book == name.upper())):
        # space in book name don't work for hyperlinks, mangle them
            book_mangled = book.replace(" ", ";")
            print "book is ", book
            books.append((book, "/mybooks/"+book_mangled))

    return books

def show_book():
    for book in lend_books_db:
        data = lend_books_db[book]
        for i in data:
            print ("book name is ", book, "owner is:", i.owner)

def borrow_book():
    pass

def get_borrowed_books(email_addr):
    books = ["Water", "Air"]
    return books


if (__name__ == "__main__"):
    print ("all books")
    add_book("Harry Potter", "haribcva@gmail.com")
    add_book("Bhagavad Gita", "haribcva@gmail.com")
    add_book("Salesforce made easy", "chitrakris@gmail.com")

    get_books()
    print ("books owned by Hari")
    get_books(user="haribcva@gmail.com")

    print ("specific book")
    get_books(name="Harry Potter")
