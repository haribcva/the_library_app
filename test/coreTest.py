#! /home/haribala/virtenv/flask/bin/python

import unittest
import sys, os
from webtest import TestApp

sys.path.append("/home/haribala/the_library_app")
from flask_app import app
from library import *

class libraryTest(unittest.TestCase):
    def setUp(self):
        path = os.path.join("/", "home", "haribala", "the_library_app", "test")
        initDatabase(path)

    def tearDown(self):
        # close the database file; remove the database file so that tests start with clean db
        closeDatabase();
        path = os.path.join("/", "home", "haribala", "the_library_app", "test", "db", "users_database")
        os.unlink(path)
        path = os.path.join("/", "home", "haribala", "the_library_app", "test", "db", "books_database")
        os.unlink(path)

    def addbooksTest(self):
         add_data=[("Harry Potter part2", "haribcva@gmail.com"), ("Bhagavad Gita", "haribcva@gmail.com"),
                   ("Salesforce made easy", "chitrakris@gmail.com"), ("Bhagavad Gita", "chitrakris@gmail.com")]
         for each in add_data:
            #print "sending args as", each
            add_book(each[0], each[1]);

         # now read back all the books we just added
         # get_books returns [(book, url, owner, status)]
         list_of_books = get_books()
         # do some map stuff

         x = map(lambda book: (book[0], book[2]), list_of_books)
         x.sort()
         y = map(lambda book: (book[0].upper(), book[1]), add_data)
         y.sort()

         self.failUnless((map(lambda book: (book[0], book[2]), list_of_books).sort()) == (map(lambda book: (book[0].upper(), book[1]), add_data).sort()))

class webLibraryTest(unittest.TestCase):
    def setUp(self):
        self.app = TestApp(app)

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

def suite():
    suite = unittest.TestSuite()
    suite.addTest(libraryTest("addbooksTest"))
    suite.addTest(webLibraryTest("indexPageTest"))

    return (suite)

if __name__ == "__main__":
    runner = unittest.TextTestRunner()
    test_suite = suite()
    runner.run(test_suite)
