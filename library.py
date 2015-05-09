__author__ = 'haribala'

import unicodedata
import shelve

STATUS_FREE     = 0
STATUS_BORROWED = 1

class appDatabase(object):
    """ base class for the storage of books; it is expected that derived classes
    will be built on top of it implementing multiple approaches."""
    pass


""" file backed pickle is the simplest way to store the database"""
class appDatabasePickle(appDatabase):
    def __init__(self, path):
        self.db = shelve.open(path, flag="c",writeback=True)

    def store_blob(self, key, blob):
        self.db[key] = blob

class bookData:
    def __init__(self, owner_email):
        self.owner = owner_email
        self.status = STATUS_FREE
        self.borrowerData = None

class userData:
    def __init__(self, user_email, user_name, lendPref, exchangePref):
        self.user_id = user_email
        self.user_name = user_name
        self.updateUserData(lendPref, exchangePref)

    def updateUserData(self, lendPref, exchangePref):
        # all, friends only ("google+" or "facebook")
        self.lendPref = None
        if lendPref in ["All", "google+", "facebook"]:
            self.lendPref = lendPref
        self.exchangePref = None
        if exchangePref in ["All", "google+", "facebook"]:
            self.exchangePref = exchangePref

def initDatabase():
    global dbBook, dbUser

    dbBook = appDatabasePickle("./books_database")
    dbUser = appDatabasePickle("./user_database")

def normalize_unicode(string_list):
    for index, string in enumerate(string_list):
        if (type(string) is unicode):
            string_list[index] = unicodedata.normalize('NFKD', string).encode('ascii','ignore')

##### user related
def add_user(user_email, user_name, lendPref, exchangePref):
    args = [user_email, user_name, lendPref, exchangePref]
    normalize_unicode(args)
    ## unpack
    user_email, user_name, lendPref, exchangePref = args
    if user_email not in dbUser.db:
        data = userData(user_email, user_name, lendPref, exchangePref)
    else:
        print "user name already exists, ignoring: ", user_email
        data = dbUser.db[user_email]
        data.updateUserData(lendPref, exchangePref)
    dbUser.store_blob(user_email, data)

def get_user(user_id):
    try:
        user_data = dbUser.db[user_id]
        return user_data
    except KeyError:
        return None

##### user related

##### books related

def add_book(name, owner_email):
    # will initialize status as free, borrower_data as None
    # normalize name, to begin with make it to all lowercaps
    if (type(name) is unicode):
        name = unicodedata.normalize('NFKD', name).encode('ascii','ignore')
    name = name.upper()
    if name in dbBook.db:
        # book exits; make sure the same person is not adding it again
        blob = dbBook.db[name]
        for each in blob:
            if (each.owner == owner_email):
                ## duplicate insertion from same owner, return
                return False

        ## add it to the database
        data = bookData(owner_email)
        blob.append(data)
    else:
        ## add it to the database
        blob = [bookData(owner_email)]

    dbBook.store_blob(name, blob)
    return True

def remove_book():
    pass

def get_books(user=None, name=None):
    books = []
    for book in dbBook.db:
        blob = dbBook.db[book]
        for data in blob:
            if ((user is None and name is None) or (user is not None and data.owner == user) or (name is not None and book == name.upper())):
        # space in book name don't work for hyperlinks, mangle them
                book_mangled = book.replace(" ", ";")
                books.append((book, "/mybooks/"+book_mangled,data))

    return books

def borrow_book():
    pass

def get_borrowed_books(email_addr):
    books = ["Alice in wonderland"]
    return books


def get_borrowable_books(current_user):
    # books_url = [("Water","/mybooks/water"), ("Air", "/mybooks/air")]
    books_url = []
    ## Walkthrough books database
    ## for each book, 
    ##    identify its owner.
    ##    look in the user database for that owner.
    ##    check the permission level that the user has given
    ##    if perm == ALL, add this book to the database.
    ##    if perm is "google+" or "facebook", check local dict if we have recently made a "user_to_friends_list" mapping
    ##    Else, make the vendor API call to get list of friends for that user.
    ##    for optimization reasons, create a dictionary where we store the "{user}: {friends_list}" mapping
    ##    check the mapping dict, see is current_user belongs to the group; if so add the book; 

    for book in dbBook.db:
        book_list = dbBook.db[book]
        for book_data in book_list:
            if (book_data.owner == current_user):
                ## this book is owned by the current_user, no point in him borrowing it
                continue

            if (book_data.status != STATUS_FREE):
                continue

            owner = dbUser.db[book_data.owner]
            if (owner.lendPref == "All"):
                books_url.append((book, "/mybooks/"+book))
            else:
                print ("Other Lending Preference not implemented, adding the book anyway")
                books_url.append((book, "/mybooks/"+book))

    return books_url

def regex_search_borrowable_books(current_user, search_string):
    books_url = [("Tintin","/mybooks/Tintin"), ("Land", "/mybooks/land")]
    return books_url

if (__name__ == "__main__"):
    initDatabase()

    add_data=[("Harry Potter part2", "haribcva@gmail.com"), ("Bhagavad Gita", "haribcva@gmail.com"),
              ("Salesforce made easy", "chitrakris@gmail.com"), ("Bhagavad Gita", "chitrakris@gmail.com")]
    for each in add_data:
        print "sending args as", each
        add_book(each[0], each[1]);

    print ("all known books:")

    test_data = [{}, {'user':'haribcva@gmail.com'}, {'user':'chitrakris@gmail.com', 'name':'Bhagavad Gita'},
                     {'user':'chitrakris@gmail.com'}]
    for each in test_data:
        print "sending args as: ", each
        if 'user' in each and 'name' in each:
            list_of_books = get_books(user=each['user'], name=each['name'])
        elif 'user' in each:
            list_of_books = get_books(user=each['user'])
        elif 'name' in each:
            list_of_books = get_books(name=each['name'])
        else:
            list_of_books = get_books()

        for book in list_of_books:
            if (book[2].status == 0):
                str = "FREE"
            else:
                str = "BORRROWED"
            print("Name: ", book[0], "owner:", book[2].owner, "Status: ", str)


    #### user related tests

    add_user_test_data = [
                          ("haribcva@gmail.com", "Hari Balasubramanian", "All", "All"),
                          ("chitrakris@gmail.com", "Chitra Krishnan", "google+", "google+"),
                          ("chitrakris@gmail.com", "Chitra Krishnan", "google+", "All")
                        ]

    for each in add_user_test_data:
        print "adding user: ", each
        add_user(each[0], each[1], each[2], each[3])

    user_list = ["haribcva@gmail.com", "chitrakris@gmail.com", "nobody"]
    for user_id in user_list:
        user_info = get_user(user_id)
        if (user_info):
            print "user_info exists: ", user_info.user_id, "with name", user_info.user_name, "shares with ", user_info.lendPref, "exchanges with ", user_info.exchangePref
        else:
            print "user_info does not exist: ", user_id


    ###### borrowing related tests
    books = get_borrowable_books("haribcva@gmail.com")
    for book_url in books:
        print "Book ", book_url[0], "is borrowable"
