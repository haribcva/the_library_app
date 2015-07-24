#! /usr/bin/env python

######## conn.execute vs cursor.execute
######## no "commit" is done, but still database has the data
######### dictionary cursor vs tuple curor
# examine conn and cursor so that we identify what can be done with them
# rollback
# SET or update operations
# metadata
# execute_many
# sqlite3.PARSE_DECLTYPES


# SELECT table1.column1, table2.column2 FROM table1, table2 WHERE table1.column1 = table2.column1;
#SELECT table1.column1, table2.column2 FROM table1, table2, table3 WHERE table1.column1 = table2.column1 AND table1.column1 = table3.column1;
#SELECT table1.column1, table2.column2 FROM table1 INNER JOIN table2
#                    ON table1.column1 = table2.column1;
#http://www.techrepublic.com/article/sql-basics-query-multiple-tables/1050307/


#sqlite3 is the CLI command that allows us to examine the DB tables

import os
import sqlite3
import code

db_filename = 'library.db' 
schema_filename = 'schema.sql'

def create_sql_database():
    # has 2 tables, books and users
    db_is_new = not os.path.exists(db_filename) 
    conn = sqlite3.connect(db_filename)

    if db_is_new:
        print 'Need to create schema'
        with open(schema_filename, 'rt') as f:
            schema = f.read()
        conn.executescript(schema)
        print 'Database opened, schema run.'

        print 'adding some books to start off the db'
        add_some_books(conn)
        print 'added some books to start off the db'
        add_some_users(conn)
    else:
        print 'Database exists, assume schema does, too.'

    return (conn)

def add_some_books(conn):
    print 'Adding some data'

    conn.execute("""
          insert into db_books (book_name, owner_email, description, status, borrower_email, deadline)
          values ('Harry Potter', 'haribcva@gmail.com', 'Varsha book', 0, 'None', '2016-01-01')
        """)
 
    conn.execute("""
          insert into db_books (book_name, owner_email, description, status, borrower_email, deadline)
          values ('Harry Potter', 'chitrakris@gmail.com', 'Chitra book', 0, 'None', '2016-01-01')
        """)
 
    conn.execute("""
          insert into db_books (book_name, owner_email)
          values ('Learn Python', 'chitrakris@gmail.com')
        """)

    conn.commit()
    print "all books added" 

def add_some_users(conn):
    print 'Adding some data'
    conn.execute("""
          insert into db_users (user_email, user_name, lend_pref, exchange_pref)
          values ('haribcva@gmail.com', 'Hari Balasubramanian', 0, 0)
        """)

    conn.execute("""
          insert into db_users (user_email, user_name, lend_pref, exchange_pref)
          values ('chitrakris@gmail.com', 'Chitra Krishnan', 0, 0)
        """)

    conn.commit()
    print "all users added" 


def close_db(conn):
    conn.close()

def show_all_books(conn):
    cursor = conn.cursor()
    cursor.execute("""
    select * from db_books
    """)

    print ("data from book table is: ")
    for row in cursor.fetchall():
        print (row)

    return (row)

def show_all_users(conn):
    cursor = conn.cursor()
    cursor.execute("""
    select * from db_users
    """)

    print ("data from user table is: ")
    for row in cursor.fetchall():
        print (row)

    return (row)


# the logic of Controller and Model has been mixed in this function; it needs to be separated
# out cleanly.
def borrow_book(conn, book_name, book_owner, borrower):
    # make sure book exists, it is the only book
    # its status must be free
    # write back status as BUSY, and borrower info in "books db"
    # update book_owner
    cursor = conn.cursor()
    conn.row_factory = sqlite3.Row

    cursor.execute("""
                    select * from db_books where book_name = :book AND owner_email = :email
                    """, {'book': book_name, 'email': book_owner})

    answer = cursor.fetchall()

    if (len(answer) == 0):
        print ("book was not found:", book_name,  " owner:", book_owner)
        return (False)

    if (len(answer) > 1):
        print ("multiple books was found:", book_name,  " owner:", book_owner)
        return (False)

    print "borrow books: book found, making other checks"

    # is status free?
    book_data = answer[0]

    if (book_data['status'] != 0):
        print ("incorrect status for the book")
        return (False)

    # check if borrower exists

    cursor.execute("""
    select count_pending from db_users where user_email = :borrower
            """, {'borrower':borrower})

    answer = cursor.fetchall()

    if (len(answer) == 0):
        print ("borrower was not found:", borrower)
        return (False)

    # only one row in answer; as only one column was requested a tuple with only element will be returned, needs to be unpacked.
    (borrow_count,) = answer[0]

    print ("for borrower ", borrower, " borrow count is ", borrow_count)

    # check if the borrow count is not more than 3

    if (borrow_count > 3):
        print ("too many books outstanding to be approved for: ", borrower)
        return False
    
    # time to write back status as Busy and borrower

    query = "update db_books set status = :status, borrower_email = :borrower_email where book_name = :book_name AND owner_email = :owner"
    cursor.execute(query, {'status':1, 'borrower_email':borrower, 'book_name':book_name, 'owner':book_owner})

    # need to update the borrower db with increased count of pending books....
    borrow_count = borrow_count + 1
    query = "update db_users set count_pending = :count where user_email = :borrower_email"
    cursor.execute(query, {'count':borrow_count, 'borrower_email':borrower})

    # commit must be done exactly once for various db for operations to be atomic;
    conn.commit()

def add_books_dynamic(conn, value):
    # value must be a tuple of rows in right order
    # we must know the number of tuple elements so we can unpack cleanly

    try:
        cursor = conn.cursor()

        cursor.execute("""
           insert into db_books (book_name, owner_email) values (?, ?)
                """, value)
        conn.commit()

    except sqlite3.IntegrityError:
        ## duplicate value, log an error
        print ("duplicate insert, ignored!!")
        return False

    finally:
        return True

# code duplicated from ../dbmodel.py
class userData:
    def __init__(self, user_email, user_name, lendPref, exchangePref):
        self.user_id = user_email
        self.user_name = user_name
        self.updateUserData(lendPref, exchangePref)
        # all of the following data needs to be made consistent of form [(bookname, user_id)]

        self.count_owned = 0
        self.ownedBooks = []

        #a list of books that this person has borrowed
        self.count_borrowed = 0
        self.borrowedBooks = []
        # a list of books that this person has reserved ie books pending approval by owner of that book
        self.count_pending = 0
        self.reservedBooks = []
        # a list of tuples of form (bookname, borrower_id): identifies list of books that needs to be approved for lending
        self.approveBooks = []
        #list of tuples of form (bookname, borrower_id): identifies list of books that has been lent
        self.lentBooks = []

    def updateUserData(self, lendPref, exchangePref):
        # all, friends only ("google+" or "facebook")
        self.lendPref = None
        #if lendPref in ["All", "google+", "facebook"]:
        if lendPref in [0, 1, 2]:
            self.lendPref = lendPref
        self.exchangePref = None
        #if exchangePref in ["All", "google+", "facebook"]:
        if exchangePref in [0, 1, 2]:
            self.exchangePref = exchangePref

# return object of userData:
def dbAccess_getUserData(conn, email_id):

    # see to it that we can use dict style to get access to rows
    conn.row_factory = sqlite3.Row

    #somehow we need to obtain the conn somehow....How???
    #each session needs to have its own database handle
    #when a session is formed (ie after login), we must have the session handle
    cursor = conn.cursor()

    cursor.execute("""
    select * from db_users where user_email = :borrower
            """, {'borrower':email_id})

    row = cursor.fetchall()

    if (len(row) == 0):
        print ("borrower was not found:", email_id)
        return (None)

    print "user row is ", row,  "type is ", type(row)
    row = row[0]
    user = userData(email_id, row['user_name'], row['lend_pref'], row['exchange_pref'])
    return (user)

# store the entire row for a given id
# is the data an object of class userData
def dbAccess_storeUserData(conn, email_id, data):
    # need to handle case where user is not present already.
    query = "update db_users set user_name = :user_name, lend_pref = :lend_pref, exchange_pref = :exchange_pref, count_borrowed = :count_borrowed, count_pending = :count_pending where user_email = :email_id"
    cursor = conn.cursor()
    cursor.execute(query, {'email_id':email_id, 'user_name':data.user_name, 'lend_pref':data.lendPref, 'exchange_pref':data.exchangePref, 'count_borrowed':data.count_borrowed, 'count_pending':data.count_pending})
    conn.commit()

def form_user(row):
    user = userData(row['user_email'], row['user_name'], row['lend_pref'], row['exchange_pref'])
    return (user)

# return iterable of all users present;
def dbAccess_getUsersList(conn):

    users_list = []
    # first query users db
    # a list of dbUser object needs to be returned.
    # tricky part is constructing borrowedBooks and reservedBooks.
    # dbUser also needs to have "lentBooks" and "pendingApproval" books.
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    cursor.execute("""
    select * from db_users order by user_name
            """)

    row = cursor.fetchall()

    users_list = [form_user(user) for user in row]

    #base info is filled, but need to fill in other data

    for user in users_list:
        # in book_db find all the books this user owns, borrowed, lent, reserved etc...
        query = """
                select book_name, status, owner_email, borrower_email from db_books where owner_email = :user_email OR borrower_email = :user_email
                """
        cursor.execute(query, {'user_email':user.user_id})
        book_row = cursor.fetchall()
        if (len(book_row) == 0):
            # this user has no references in book db, constructor for
            # dbUser should have set zero and None references, so nothing to do
            continue
        for book in book_row:
            book_name = book['book_name']
            book_status = book['status']
            book_owner = book['owner_email']
            book_borrower = book['borrower_email']

            if (book_owner == user.user_id):
                user.ownedBooks.append(book_name)
                if (book_status == 1):
                    user.lentBooks.append(book_name)
                if (book_status == 2):
                    user.pendingBooks.append(book_name)

            if (book_borrower == user.user_id):
                if (book_status == 1):
                    user.borrowedBooks.append(book_name)
                if (book_status == 2):
                    user.reservedBooks.append(book_name)

    return (users_list)

#### Book related....
class bookData:
    def __init__(self, owner_email, status=None):
        self.owner = owner_email
        if (status == None):
            self.status = STATUS_FREE
        else:
            self.status = status
        # who has borrowed this book and related info (due date etc)
        self.borrowerData = None
        # other data that can be added are isbn code

def dbAccess_isBookPresent(conn, book_name, owner=None):
    cursor = conn.cursor()

    # must replace query with COUNT(*)
    if (owner != None):
        cursor.execute("""
        select * from db_books where book_name = :book AND owner_email = :email
        """, {'book': book_name, 'email': owner})
    else:
        cursor.execute("""
        select * from db_books where book_name = :book
        """, {'book': book_name})

    answer = cursor.fetchall()
   
    if (len(answer) == 0):
        return (False)
    else:
        return (True)

#must return List of bookData for each book found with book_name
def dbAccess_getBookData(conn, book_name):
    ret_data = []
    cursor = conn.cursor()

    cursor.execute("""
        select * from db_books where book_name = :book
        """, {'book': book_name})

    book_row = cursor.fetchall()
    for book in book_row:
        print "getBookData: ", book['book_name'], book['status'], book['description'], book['owner_email']
        ret_data.append(bookData(book['owner_email'], book['status']))

    return ret_data

# list of all books
def dbAccess_getBooksList(conn):
    ret_data = []
    cursor = conn.cursor()

    cursor.execute("""
        select book_name from db_books
        """)

    book_row = cursor.fetchall()
    for book in book_row:
        print "getBooksList: ", book['book_name']
        ret_data.append(book['book_name'])

    return ret_data

def dbAccess_storeBookData(conn, book_name, data):
    cursor = conn.cursor()
    # extrace email from data; form full key of book_name, owner_email;
    # check if record exists; if not create it; if exists, update it.
    value = (book_name, data.owner, data.status)
    if (dbAccess_isBookPresent(conn, book_name, data.owner) == False):
        cursor.execute("""
           insert into db_books (book_name, owner_email, status) values (?, ?, ?)
                """, value)
    else:
        query = "update db_books set status = :status where book_name = :book_name AND owner_email = :owner"
        cursor.execute(query, {'status':data.status, 'book_name':book_name, 'owner':data.owner})

    conn.commit()

if (__name__ == "__main__"):
    conn = create_sql_database()

    #add_some_books(conn)
    value = ("SQL programming", "haribcva@gmail.com")
    add_books_dynamic(conn, value)

    row = show_all_books(conn)

    #if (is_book_present(conn, "Harry Potter", "chitrakris@gmail.com") is True):
    #    print ("Book found")
    #else:
    #    print ("Book not found")

    conn.row_factory = sqlite3.Row
    #print "After changing row_factory...."
    row = show_all_books(conn)

    #print "testing Row Factory.... name is: ", row['book_name'], row['owner_email']
    #code.interact(local=globals())


    print "to show all users so far.."
    show_all_users(conn)

    print "To test borrow books ...."

    ret = borrow_book(conn, "SQL programming", "haribcva@gmail.com", "chitrakris@gmail.com")
    if (ret == False):
        print "Borrow of books failed"
    else:
        print "Borrow of books was ok, showing updated books and user database....."
        show_all_books(conn)
        show_all_users(conn)

    print "to get user Object..."
    user = dbAccess_getUserData(conn, "haribcva@gmail.com")
    print "got user object name is ", user.user_name

    user.lendPref = 2
    dbAccess_storeUserData(conn, "haribcva@gmail.com", user)

    user = dbAccess_getUserData(conn, "haribcva@gmail.com")
    print "got user lendPref is ", user.lendPref

    users_info =  dbAccess_getUsersList(conn)
    for each in users_info:
        print "user: ", each.user_name, " owns ", each.ownedBooks, " has lent ", each.lentBooks, " has borrowed ", each.borrowedBooks, " has requested", each.reservedBooks, "has to approve ", each.approveBooks

    dbAccess_getBookData(conn, "SQL programming")
    #dbAccess_getBooksList(conn)

    data = bookData("haribcva@gmail.com", 0)
    dbAccess_storeBookData(conn, "SQL programming", data)
    dbAccess_storeBookData(conn, "Data center ethernet", data)

    dbAccess_getBooksList(conn)
    dbAccess_getBookData(conn, "SQL programming")
    dbAccess_getBookData(conn, "Harry Potter")

    close_db(conn)
