import os.path
import unicodedata
import shelve

database_list = []
dbBook = None
dbUser = None

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

    def close_database(self):
        self.db.close()
    # it would be perfect case to introduce property to capture the member
    # variables. The property underlying code would make db access depending on
    # type of underlying database type.

def initDatabase(path):
    global dbBook
    global dbUser
    db_books_path = os.path.join(path,"db", "books_database");
    dbBook = appDatabasePickle(db_books_path)
    database_list.append(dbBook);

    db_users_path = os.path.join(path,"db", "users_database");
    dbUser = appDatabasePickle(db_users_path)
    database_list.append(dbUser);

    dbAccess_dumpBookDatabase()
    dbAccess_dumpUserDatabase()
    return (dbUser, dbBook)

def getDatabase():
    return (dbUser, dbBook)


def closeDatabase():
    for db in database_list:
        db.db.close()

def dbAccess_isUserPresent(email_id):
    # add code like if dbType is Pickle, then....
    # else if dbType is SQL Lite....
    return (email_id in dbUser.db)

# return data: class userData
def dbAccess_getUserData(email_id):
    # add code like if dbType is Pickle, then....
    # else if dbType is SQL Lite....
    return (dbUser.db[email_id])

# store the entire row for a given id
def dbAccess_storeUserData(email_id, data):
    dbUser.store_blob(email_id, data)

# return iterable of all users present;
def dbAccess_getUsersList():
    # the entire database is a dictionary; returning the db is iterable effectively masking it
    return (dbUser.db)


#Book db related.
def dbAccess_isBookPresent(book_name):
    # add code like if dbType is Pickle, then....
    # else if dbType is SQL Lite....
    return (book_name in dbBook.db)

# it is expected this is list of data for a given book_name
def dbAccess_getBookData(book_name):
    return (dbBook.db[book_name])

# list of all books
def dbAccess_getBooksList():
    return (dbBook.db)

def dbAccess_storeBookData(key, data):
    # this needs to check if the key already exists; if so, it needs to be append the data.

    if (key in dbBook.db):
        #just append it
        dbBook.db[key].append(data)
    else:
        #make a list with one element & add it
        dbBook.db[key] = [data]

    # the correct design would be make (book_name and owner_id) as joint keys of the database.
    # This can be possible in a regular database, but in a Pickle based database, the key can only
    # be a string. This forces, in Pickle db, for the bookname alone as the key and keep a list of
    # data, where data stores the owner_id. The database abstraction layer has to perform this
    # magic.
    #dbBook.store_blob(book_name, data)

#### debug utilities
def dbAccess_dumpBookDatabase():
    print "dumping books database..."
    for book in dbBook.db:
        print "name: ", book, " data: ", dbBook.db[book]
    print "dumped books database..."

def dbAccess_dumpUserDatabase():
    print "dumping users database..."
    for user in dbUser.db:
        print "name: ", user, " data: ", dbUser.db[user]
    print "dumped books database..."
