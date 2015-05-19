#! /home/haribala/virtenv/flask/bin/python

import unittest
import sys, os
from webtest import TestApp

sys.path.append("/home/haribala/the_library_app")
from flask_app import app
from library import *

def addBooksTest(self):
    add_data=[("Harry Potter part2", "haribcva@gmail.com"), ("Bhagavad Gita", "haribcva@gmail.com"),
                   ("Salesforce made easy", "chitrakris@gmail.com"), ("Bhagavad Gita", "chitrakris@gmail.com")]
    for each in add_data:
            #print "sending args as", each
            add_book(each[0], each[1])

    # now read back all the books we just added
    # get_books returns [(book, url, owner, status)]
    list_of_books = get_books()
    # do some map stuff

    #x = map(lambda book: (book[0], book[2]), list_of_books)
    #x.sort()
    #y = map(lambda book: (book[0].upper(), book[1]), add_data)
    #y.sort()

    self.failUnless((map(lambda book: (book[0], book[2]), list_of_books).sort()) == (map(lambda book: (book[0].upper(), book[1]), add_data).sort()))

    # to add get_books with email_addr and get_books with name & email addr
def addUsersTest(self):
    add_user_test_data = [
                          ("haribcva@gmail.com", "Hari Balasubramanian", "All", "All"),
                          ("chitrakris@gmail.com", "Chitra Krishnan", "google+", "google+"),
                          ("chitrakris@gmail.com", "Chitra Krishnan", "google+", "All")
                        ]

    for each in add_user_test_data:
        # print "adding user: ", each
        add_user(each[0], each[1], each[2], each[3])

    user_list = ["haribcva@gmail.com", "chitrakris@gmail.com"]
    list_of_users = []

    for user_id in user_list:
        user_info = get_user(user_id)
        list_of_users.append(user_info)

    # check the values, 3 entries in list_of_users; first for haribcva, second chitrakris, last one must be none
    x = map(lambda user: user.user_id, list_of_users)
    x.sort()
    x = set(x)
    y = map(lambda user: user[0], add_user_test_data)
    y.sort()
    y = set(y)

    # print "going to compare x and y", x, y

    self.failUnless (x == y)

def borrowBooksTest(self):
    bookname = "Harry Potter part2"
    owner_email = "haribcva@gmail.com"
    borrower_email = "chitrakris@gmail.com"

    status, msg = borrow_this_book(bookname.upper(), owner_email, borrower_email)
    self.failUnless(status == True and msg == "Book borrow ok")

class libraryTest(unittest.TestCase):
    def setUp(self):
        path = os.path.join("/", "home", "haribala", "the_library_app", "test")
        initDatabase(path);
        initEmailSubsystem();

    def tearDown(self):
        # close the database file; remove the database file so that tests start with clean db
        closeDatabase();
        path = os.path.join("/", "home", "haribala", "the_library_app", "test", "db", "users_database")
        os.unlink(path)
        path = os.path.join("/", "home", "haribala", "the_library_app", "test", "db", "books_database")
        os.unlink(path)
        endEmailSubsystem()

    def allBooksTest(self):
         addBooksTest(self)
         addUsersTest(self)
         borrowBooksTest(self)


class webLibraryTest(unittest.TestCase):
    def setUp(self):
        self.app = TestApp(app)
        ## hack to get get_all_users working; database would be inited by the flask_app anyway
        #path = os.path.join("/", "home", "haribala", "the_library_app")
        #initDatabase(path);

    def tearDown(self):
        self.app = None

    def indexPageTest(self):
        resp = self.app.get('/') 
        self.failUnless(resp.status_code == 200, "failed to get index Page")
        self.failUnless(resp.mustcontain('lend_books') is  None)
        self.failUnless(resp.mustcontain('exchange_books') is  None)
        self.failUnless(resp.mustcontain('donate_books') is  None)
        form = resp.forms[0]
        self.failUnless(form is not None)
        resp = form.submit('donate_books')
        self.failUnless(resp.status_code == 302)

    def fakeLoginTest(self): 
        resp = self.app.get('/fake_login?name=hari&email=haribcva@gmail.com') 
        self.failUnless(resp.status_code == 302)

        resp = self.app.get('/fake_login?name=chitra&email=chitrakris@gmail.com') 
        self.failUnless(resp.status_code == 302)

    def lendbooksPageTest(self):
        books = ["Harry Potter", "Bhagavad Gita", "Salesforce design", "Master Python", "Magic tree house", "Tennis", "Land", "Water", "Air", "Hope"]
        for book in books:
            resp = self.app.get('/lend_books')
            self.failUnless(resp.status_code == 200, "failed to get lend_books Page")
            self.failUnless(len(resp.forms) == 4, " did not have 4 forms as expected")
            # 2 forms don't have id and so the key are 0 and 1; two forms have id and key is their id
            form = resp.forms[0]
            self.failUnless(form is not None)
            form['bookname0'] = book
            resp = form.submit()
            self.failUnless(resp.status_code == 302)

    def borrowthisPageTest(self):
        resp = self.app.get('/borrowthis?name=HOPE&owner=haribcva@gmail.com')
        print resp, resp.html

def suite():
    suite = unittest.TestSuite()
    # direct test all done in one go as tearDown phase cleans up the database
    suite.addTest(libraryTest("allBooksTest"))

    suite.addTest(webLibraryTest("indexPageTest"))
    suite.addTest(webLibraryTest("fakeLoginTest"))
    suite.addTest(webLibraryTest("lendbooksPageTest"))
    suite.addTest(webLibraryTest("borrowthisPageTest"))

    return (suite)

if __name__ == "__main__":
    runner = unittest.TextTestRunner()
    test_suite = suite()
    runner.run(test_suite)
