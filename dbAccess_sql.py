import os
import os.path
import sqlite3

DB_SQL = 1

from dbAccess import appDatabase
from dbmodel import userData
from dbmodel import bookData

class appDatabaseSql(appDatabase):
    def __init__(self, basedir) :
        super(appDatabaseSql, self).__init__(DB_SQL)
        #appDatabaseSql.__init__(self, 1)

        db_filename = os.path.join(basedir, 'db', 'library.db')
        schema_filename = os.path.join(basedir, 'db', 'schema.sql')

        print ("to executed schema....BBBBB:", db_filename, schema_filename)
        x =  os.path.exists(db_filename)
        print ("x is :", x)

        if not os.path.exists(db_filename):
        #if True:
            # need to create db
            with open(schema_filename, 'rt') as f:
                schema = f.read()
            self.conn = sqlite3.connect(db_filename)
            self.conn.executescript(schema)
            print ("executed schema....AAAAAA:", db_filename, schema_filename)
        else:
            self.conn = sqlite3.connect(db_filename)


    # get rows as dict-friendly style
        self.conn.row_factory = sqlite3.Row
        self.cursor = self.conn.cursor()

    def dbAccess_closeDb(self):
        self.conn.close()

    ### begin userDB related
    def dbAccess_isUserPresent(self, email_id):
        self.cursor.execute("""
           select * from db_users where user_email = :email_id
           """, {'email_id': email_id})

        answer = self.cursor.fetchall()
        if (len(answer) == 0):
            return (False)
        else:
            return (True)

    def dbAccess_getUserData(self, email_id):
        self.cursor.execute("""
            select * from db_users where user_email = :borrower
            """, {'borrower':email_id})

        row = self.cursor.fetchall()

        if (len(row) == 0):
            return (None)

        row = row[0]
        user = userData(email_id, row['user_name'], row['lend_pref'], row['exchange_pref'], row['gplus_id'], row['facebk_id'])
        return (user)

    def dbAccess_storeUserData(self, email_id, data):
        if (self.dbAccess_isUserPresent(email_id) == False):
            value = (data.user_id, data.user_name, data.lendPref, data.exchangePref, data.gplus_id, data.facebk_id)
            print "beforeAdding to DB:", value
            query = """
               insert into db_users (user_email, user_name, lend_pref, exchange_pref, gplus_id, facebk_id) values (?, ?, ?, ?, ?, ?)
                """
            self.cursor.execute(query, value)
        else:
            query = "update db_users set user_name = :user_name, lend_pref = :lend_pref, exchange_pref = :exchange_pref, count_borrowed = :count_borrowed, count_pending = :count_pending where user_email = :email_id"
            self.cursor.execute(query, {'email_id':email_id, 'user_name':data.user_name, 'lend_pref':data.lendPref, 'exchange_pref':data.exchangePref, 'count_borrowed':data.count_borrowed, 'count_pending':data.count_pending})
        self.conn.commit()

    def dbAccess_getUsersList(self):
       def form_user(row):
           user = userData(email_id, row['user_name'], row['lend_pref'], row['exchange_pref'], row['gplus_id'], row['facebk_id'])
           return (user)

       users_list = []

       self.cursor.execute("""
              select * from db_users order by user_name
            """)

       row = self.cursor.fetchall()

       users_list = [form_user(user) for user in row]

       # A Join could be useful here.... to do
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

    ### end userDB related

    # begin Book db related.
    def dbAccess_isBookPresent(self, book_name, owner=None):
        # must replace query with COUNT(*)
        if (owner != None):
            self.cursor.execute("""
             select * from db_books where book_name = :book AND owner_email = :email
             """, {'book': book_name, 'email': owner})
        else:
            self.cursor.execute("""
             select * from db_books where book_name = :book
             """, {'book': book_name})

        answer = self.cursor.fetchall()
   
        if (len(answer) == 0):
            return (False)
        else:
            return (True)

    def dbAccess_getBookData(self, book_name):
        ret_data = []

        self.cursor.execute("""
            select * from db_books where book_name = :book
            """, {'book': book_name})

        book_row = self.cursor.fetchall()
        for book in book_row:
            print "getBookData: ", book['book_name'], book['status'], book['description'], book['owner_email']
            ret_data.append(bookData(book['owner_email'], book['status']))

        return ret_data

    def dbAccess_getBooksList(self):
        ret_data = []
        self.cursor.execute("""
            select book_name from db_books
            """)

        book_row = self.cursor.fetchall()
        for book in book_row:
            print "getBooksList: ", book['book_name']
            ret_data.append(book['book_name'])

        return ret_data


    def dbAccess_storeBookData(self, book_name, data):
        value = (book_name, data.owner, data.status)
        if (self.dbAccess_isBookPresent(book_name, data.owner) == False):
            self.cursor.execute("""
               insert into db_books (book_name, owner_email, status) values (?, ?, ?)
                """, value)
        else:
            query = "update db_books set status = :status where book_name = :book_name AND owner_email = :owner"
            self.cursor.execute(query, {'status':data.status, 'book_name':book_name, 'owner':data.owner})

        self.conn.commit()

    # end Book db related.
