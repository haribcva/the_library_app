import os.path
import unicodedata
import shelve
import shelve

from dbAccess import appDatabase
DB_SHELVE = 0

""" file backed pickle is the simplest way to store the database"""
class appDatabaseShelve(appDatabase):
    def __init__(self, basedir):
        super(appDatabaseShelve, self).__init__(DB_SHELVE)

        db_books_path = os.path.join(basedir,"db", "books_database");
        self.dbBook = shelve.open(db_books_path, flag="c",writeback=True)

        db_books_path = os.path.join(basedir,"db", "user_database");
        self.dbUsers = shelve.open(db_books_path, flag="c",writeback=True)

    def close_database(self):
        self.dbUsers.close()
        self.dbBooks.close()
    # it would be perfect case to introduce property to capture the member
    # variables. The property underlying code would make db access depending on
    # type of underlying database type.

    def dbAccess_isUserPresent(self, email_id):
        return (email_id in self.dbUsers)

    # return data: class userData
    def dbAccess_getUserData(email_id):
        return (self.dbUsers.get(email_id, None))

    # store the entire row for a given id
    def dbAccess_storeUserData(self,email_id, data):
        self.dbUsers[key] = blob

    # return iterable of all users present;
    def dbAccess_getUsersList(self):
        # the entire database is a dictionary; returning the db is iterable effectively masking it
        return (self.dbUsers)

    #Book db related.
    def dbAccess_isBookPresent(self, book_name):
        # add code like if dbType is Pickle, then....
        # else if dbType is SQL Lite....
        return (book_name in self.dbBooks)

    # it is expected this is list of data for a given book_name
    def dbAccess_getBookData(self, book_name):
        return (dbBooks.get(book_name, None))

    # list of all books
    def dbAccess_getBooksList(self):
        return (self.dbBooks)

    def dbAccess_storeBookData(self, key, data):
    # this needs to check if the key already exists; if so, it needs to be append the data.

        if (key in self.dbBooks):
        #just append it
            self.dbBooks[key].append(data)
        else:
        #make a list with one element & add it
            self.dbBooks[key] = [data]

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
