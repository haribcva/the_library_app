__author__ = 'haribala'

# other choice of data struc is MultiDict used by flask
# { name: [bookInfoClass]
lend_books_db = {}

# borrowerData = [borrower_email, date_borr, date_to_return, times_borrowed]

STATUS_FREE     = 0
STATUS_BORROWED = 1

class bookInfoClass:
    def __init__(self, owner_email):
        self.owner = owner_email
        self.status = STATUS_FREE
        self.borrowerData = None

def add_book(name, owner_email):
    # will initialize status as free, borrower_data as None
    # normalize name, to begin with make it to all lowercaps
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
        lend_books_db[name].append(data)
    else:
        ## add it to the database
        data = bookInfoClass(owner_email)
        lend_books_db[name] = [data]

    return True

def remove_book():
    pass

def get_books():
    books = []
    for book in lend_books_db:
        books.append((book, "/mybooks/water/"))

    return books

def show_book():
    for book in lend_books_db:
        data = lend_books_db[book]
        for i in data:
            print ("book name is ", book, "owner is:", i.owner)

def borrow_book():
    pass

def add_book_to_database(bookname, user_name):
    # write to a file
    try:
         line = bookname + ":" + user_name
         outFile = open('output.txt', mode='w')
         outFile.write(line)
    except:
        pass

    outFile.close()

def handleBook(book,user="default"):
    print (book)
