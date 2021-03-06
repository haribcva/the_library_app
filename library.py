__author__ = 'haribala'

import unicodedata
import shelve
import os.path

from multiprocessing import JoinableQueue, Process
from dbmodel import *
from dbAccess import *

#database_list = []
#dbBook = None 
#dbUser = None

#cannot import flask_app due to circular dependency....
#only place something is needed from flask_app is the logging functions.
#so workaround is to import flask_app in these functions and also
#not to call logging in initialization code in this module.
def log_error(args):
    from flask_app import app
    app.logger.error(args)
    assert False

def log_warning(args):
    from flask_app import app
    app.logger.warning(args)

def log_info(args):
    from flask_app import app
    app.logger.info(args)

#class appDatabase(object):
#    """ base class for the storage of books; it is expected that derived classes
#    will be built on top of it implementing multiple approaches."""
#    pass


#""" file backed pickle is the simplest way to store the database"""
#class appDatabasePickle(appDatabase):
#    def __init__(self, path):
#        self.db = shelve.open(path, flag="c",writeback=True)

#    def store_blob(self, key, blob):
#        self.db[key] = blob

#    def close_database(self):
#        self.db.close()
    # it would be perfect case to introduce property to capture the member
    # variables. The property underlying code would make db access depending on
    # type of underlying database type.

#def initDatabase(path):
    #global dbBook, dbUser

#    db_books_path = os.path.join(path,"db", "books_database");
#    dbBook = appDatabasePickle(db_books_path)
#    database_list.append(dbBook);

#    init_user_database():
#    db_users_path = os.path.join(path,"db", "users_database");
#    dbUser = appDatabasePickle(db_users_path)
#    database_list.append(dbUser);

#def closeDatabase():
#    for db in database_list:
#        db.db.close()

def emailInfo(emailData):
    log_warning("sending email is not yet implemented")

def sendEmailWorker(emailQueue, replyQueue):
    proc_name = "sendEmailWorker"
    while True:
        next_task = emailQueue.get()
        if next_task is None:
            # Poison pill means shutdown
            #print '%s: Exiting' % proc_name
            emailQueue.task_done()
            break
        #print '%s: %s' % (proc_name, next_task)
        answer = emailInfo(next_task)
        emailQueue.task_done()
        replyQueue.put(answer)

    log_warning("Worker Queue, All done to die")
    return

class emailSubsystem(object):
    def __init__(self):
        ### will move to Celery eventually; with Celery, the app would be able to periodically
        # wakeup and check on replyQueue to see which emails were send, which were not and
        # what to do ...

        self.emailQueue = JoinableQueue()
        self.replyQueue = JoinableQueue()

        self.worker = Process(target=sendEmailWorker, args=(self.emailQueue, self.replyQueue))

    def start(self):
        # temporarily comment out starting a new process as it seems to leave zombies
        # and causes app not to start as max process limit is reached.
        #self.worker.start()
        return

    def shutdown(self):
        # post poison pill
        # wait on the queue to be done; ie join on emailQueue
        # wait on the worker process to die; ie join on worker

        self.emailQueue.put(None)
        self.emailQueue.join()
        self.worker.join()

def initEmailSubsystem():
    global emailSystem

    emailSystem = emailSubsystem()
    emailSystem.start()
    
def endEmailSubsystem():
    emailSystem.shutdown()

def normalize_unicode(inputs):
    if ((type(inputs) != list)):
        if (type(inputs) is unicode):
            return (unicodedata.normalize('NFKD', inputs).encode('ascii','ignore'))
        else:
            return inputs

    ## assumed to be a list of strings
    string_list = inputs
    for index, string in enumerate(string_list):
        if (type(string) is unicode):
            string_list[index] = unicodedata.normalize('NFKD', string).encode('ascii','ignore')

##### user related
def add_user(user_email, user_name, gplus_id=None, fbook_id=None,lendPref="All", exchangePref="All"):
    args = [user_email, user_name, lendPref, exchangePref]
    normalize_unicode(args)
    ## unpack
    user_email, user_name, lendPref, exchangePref = args
    if (dbAccess_isUserPresent(user_email) == False):
    #if user_email not in dbUser.db: ### XXX replace by functions that hide DB implementation
        data = userData(user_email, user_name, lendPref, exchangePref)
    else:
        log_warning("user name already exists for {0} just updating".format(user_email))
        #data = dbUser.db[user_email]
        data = dbAccess_getUserData(user_email)
        data.updateUserData(lendPref, exchangePref)
    # dbUser.store_blob(user_email, data)
    dbAccess_storeUserData(user_email, data)

def get_user(user_id):
    try:
        #user_data = dbUser.db[user_id]
        user_data = dbAccess_getUserData(user_id)
        return user_data
    except KeyError:
        return None

def get_all_users():
    print ("Users known are:")
    list_of_users = dbAccess_getUsersList()
    #for user_name in dbUser.db:
    for user_name in list_of_users:
        user = dbAccess_getUserData(user_id)
        #user = dbUser.db[user_name]
        print (user_name, user.user_id, user.user_name, user.lendPref, user.exchangePref, user.borrowedBooks, user.reservedBooks)

##### end user related

##### begin books related

def add_book(name, owner_email):
    # will initialize status as free, borrower_data as None
    # normalize name, to begin with make it to all lowercaps
    name = normalize_unicode(name)
    owner_email = normalize_unicode(owner_email)

    name = name.upper()
    #xxx, dbBook = getDatabase()
    if dbAccess_isBookPresent(name):
    #if name in dbBook.db:
        # book exits; make sure the same person is not adding it again
        blob = dbAccess_getBookData(name)
        #blob = dbBook.db[name]
        for each in blob:
            log_warning("book {0} already exists added by {1}".format(name, each.owner))
            if (each.owner == owner_email):
                ## duplicate insertion from same owner, return
                log_error("book {0} already added by same user {1}, not adding again",format(name, each.owner))
                return False

    ## add it to the database
    data = bookData(owner_email)
    dbAccess_storeBookData(name, data)
    log_info("book {0} added for user {1} ".format(name, owner_email))

    return True

def remove_book():
    pass

# returns [(book, url, owner, status)]
def get_books(user=None, name=None):
    #print "get_books: passed: ", user, name
    if (name != None):
        # reverse mange it
        name = name.replace(";", " ")
        name = normalize_unicode(name)
        #print "after unmangling we have", name
    books = []
    #xxx, dbBook = getDatabase()
    all_books_list = dbAccess_getBooksList()
    #for book in dbBook.db:
    for book in all_books_list:
        blob = dbAccess_getBookData(book);
        #blob = dbBook.db[book]
        if (type(blob) is not list):
            continue

        for data in blob:
            if ((user is None and name is None) or (user is not None and data.owner == user) or (name is not None and book == name.upper())):
        # space in book name don't work for hyperlinks, mangle them
                book_mangled = book.replace(" ", ";")
                books.append((book, "/mybooks/"+book_mangled,data.owner,data.status))

    return books

def borrow_this_book(bookname, owner_email, borrower_email):
    # check if the borrower has already borrowed more than 3 books; if so fail
    # check if the borrower has already 3 books in reserved status; if so fail 
    # failures should send a meaningful message
    # check if the status of book is FREE: if not fail; else change status to RESERVED
    # inform back to the user that message has been sent to owner of the request
    # enque a work item that will help send an email later; owner, bookname,borrower
    # must be part of work enqueued.
    #get_all_users()
    bookname = normalize_unicode(bookname)
    borrower_email = normalize_unicode(borrower_email)
    owner_email = normalize_unicode(owner_email)
    #print "after borrowthis inputs:", bookname, borrower_email, owner_email

    ### replace by get_user api hiding database implementation
    borrower = dbAccess_getUserData(normalize_unicode(borrower_email))
    #borrower = dbUser.db.get(normalize_unicode(borrower_email), None)
    if (borrower is None):
        return False,"Borrower not known"
    owner = dbAccess_getUserData(normalize_unicode(owner_email))
    #owner = dbUser.db.get(normalize_unicode(owner_email), None)
    if (owner is None):
        return False,"Owner not known"
    if (len (borrower.borrowedBooks) > 3 or len(borrower.reservedBooks) > 3):
        return False, "Borrower limit exceeded"
    #xxx, dbBook = getDatabase()
    book_list =  dbAccess_getBookData(bookname)
    if (book_list == None):
        return False, "Book not found"
    book_data = None
    for data in book_list:
        if (data.owner == owner_email):
            book_data = data
    if book_data is None:
        return False, "Book not found with right owner"
    if (book_data.status is not STATUS_FREE):
        return False, "message 2"

    book_data.status = STATUS_RESERVED
    dbAccess_storeBookData(bookname, book_data)
    #dbBook.store_blob(bookname, book_data)

    ### update reservedBooks list in borrower User DB
    borrower.reservedBooks.append(bookname)
    dbAccess_storeUserData(borrower_email, borrower)
    #dbUser.store_blob(borrower_email, borrower)

    ### update approveBooks list in owner User DB
    owner.approveBooks.append((bookname,borrower_email))
    dbAccess_storeUserData(owner_email, owner)
    #dbUser.store_blob(owner_email, owner)

    ### form email data
    emailQueueData = (owner_email, bookname, borrower_email)
    emailSystem.emailQueue.put_nowait(emailQueueData)

    return True, "Book borrow ok"


def util_make_url(book, urlbase,borrower=None):
    book_mangled = book.replace(" ", ";")
    if (borrower):
        return((book, urlbase+book_mangled, borrower))
    else:
        return((book, urlbase+book_mangled))

def user_get_data(user_id):
    # get books borrowed sorted by due date
    # get books that have been requested so far, but not approved.
    # books that are requested to be lent
    borrowed_books = []
    requested_books = []
    approvals_needed_books = []
    
    user = dbAccess_getUserData(normalize_unicode(user_id))
    #user = dbUser.db.get(normalize_unicode(user_id), None)
    if (user == None):
        return borrowed_books, requested_books, approvals_needed_books

    borrowed_books = [util_make_url(book, "/mybooks/") for book in user.borrowedBooks]
    requested_books = [util_make_url(book, "/mypendingbooks/") for book in user.reservedBooks]
    approvals_needed_books = [util_make_url(book, "/myapprovebooks/", borrower) for book,borrower in user.approveBooks]

    return borrowed_books, requested_books, approvals_needed_books

def borrow_cancel_borrow_request(bookname, owner):
    # cancel the borrrow request; put book status back to FREE.
    # if email queue has info to be sent to owner remove that entry
    # else, send an email saying the borrower is no longer interested in the book.
    pass

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

    #xxx, dbBook = getDatabase()
    all_books = dbAccess_getBooksList()
    for book in all_books:
    #for book in dbBook.db:
        book_list = dbAccess_getBookData(book)
        #book_list = dbBook.db[book]
        print ("book is: ", book,)
        print (" book_list is: ", book_list)
        if (type(book_list) is not list):
            print ("not a list, igoring ", book)
            continue
        for book_data in book_list:
            if (book_data.owner == current_user):
                ## this book is owned by the current_user, no point in him borrowing it
                continue

            if (book_data.status != STATUS_FREE):
                continue

            try:
                owner = dbAccess_getUserData(book_data.owner)
                #owner = dbUser.db[book_data.owner]
                if (owner.lendPref == "All"):
                    book_mangled = book.replace(" ", ";")
                    books_url.append((book, "/mybooks/"+book_mangled, book_data.owner, book_data.status))
                else:
                    log_error("Other Lending Preference not implemented, adding the book anyway")
                    book_mangled = book.replace(" ", ";")
                    books_url.append((book, "/mybooks/"+book_mangled, book_data.owner, book_data.status))
            except KeyError:
                ### user not in database, log it.; till login is implemented, make this book available anyway
                book_mangled = book.replace(" ", ";")
                books_url.append((book, "/mybooks/"+book_mangled, book_data.owner, book_data.status))
                pass

    return books_url

def regex_search_borrowable_books(current_user, search_string):
    books_url=[]
    return books_url

#operation: could be one of "approve" or "reject"
#if book is None, all pending books for the user are approved or rejected.
#bookname is managled already ie capitalized and spaces replaced by ";"
def approve_books(user_id, operation, mangled_bookname=None):
    owner = dbAccess_getUserData(user_id)
    #owner = dbUser.db[user_id]
    if (owner is None):
        return ("owner not known for " + user_id)

    bookname = None
    approveData = []

    if (mangled_bookname is not None):
        bookname = mangled_bookname.replace(";", " ")

    if (bookname is not None):
        #identify the borrower
        for each in owner.approveBooks:
            if (each[0] == bookname):
                approveData = [(bookname, each[1])]
                break
    else:
        # work on all books for the approver
        # make a copy as we will have to make changes to the list maintained in 
        # the database
        approveData = list(owner.approveBooks)

    for each in approveData:
        #unpack the tuple
        book, borrower_id = each
        borrower = dbAccess_getUserData(borrower_id)
        #borrower = dbUser.db[borrower_id]
        if (borrower is None):
            # log_error are supposed to log an error and assert?
            log_error("borrower not known for " + borrower_id)
            continue
        if (operation == "approve"):
            try:
                index = owner.approveBooks.index(each)
            except ValueError:
                log_error("unexpected condition...approved book not in owner's approval list!!")
                #move on to next element...
                continue
            entry = owner.approveBooks.pop(index)
            owner.lentBooks.append(entry)
            try:
                index = borrower.reservedBooks.index(book)
            except ValueError:
                log_error("unexpected condition...approved book not in borrower's reserved list!!")
                #move on to next element...
                continue
            entry = borrower.reservedBooks.pop(index)
            borrower.borrowedBooks.append(entry)
            #supposed to send mail to borrower that owner has agreed to lend the book;
            #from implementation point of view, it is as though the book has been lent.
            #it is an core assumption that owner will honor the promise and has given the book..
            emailQueueData = (borrower_id, bookname, user_id, "approve email format to borrower from owner")
            emailSystem.emailQueue.put_nowait(emailQueueData)
        else:
            # operation is "reject".... remove book from owner's approveBooks queue & borrower's reservedBooks queue...
            owner.approveBooks.remove(each)
            borrower.reservedBooks.remove(book)
            #notify borrower that is reservation has been rejected by owner...
            emailQueueData = (borrower_id, bookname, user_id, "reject email format to borrower from owner")
            emailSystem.emailQueue.put_nowait(emailQueueData)

    # identify list of books to work on, if bookname is None
    # for each book, identify borrower
    # if operation is approve:
    #   move book from owner's "approval pending" queue to "return pending" queue.
    #   move book from borrower's "pending approval" queue to "pending return" queue
    #   send email to borrower of the transaction & return date
    # if operation is reject:
    #    remove book from owner's "approval pending"
    #    remove book from borrower's "pending approval" queue
    #    send email to borrower of the transaction.

    # perform all operations in CLEAN DATABASE approach, so that if database changes tomorrow you will be ok.
    return

######### TEST #########
if (__name__ == "__main__"):
    path = os.path.join("/", "home", "haribala", "the_library_app", "test")
    initDatabase(path)

    add_data=[("Harry Potter part2", "haribcva@gmail.com"), ("Bhagavad Gita", "haribcva@gmail.com"),
              ("Salesforce made easy", "chitrakris@gmail.com"), ("Bhagavad Gita", "chitrakris@gmail.com")]
    for each in add_data:
        print ("sending args as", each)
        add_book(each[0], each[1]);

    print ("all known books:")

    test_data = [{}, {'user':'haribcva@gmail.com'}, {'user':'chitrakris@gmail.com', 'name':'Bhagavad Gita'},
                     {'user':'chitrakris@gmail.com'}]
    for each in test_data:
        print ("sending args as: ", each)
        if 'user' in each and 'name' in each:
            list_of_books = get_books(user=each['user'], name=each['name'])
        elif 'user' in each:
            list_of_books = get_books(user=each['user'])
        elif 'name' in each:
            list_of_books = get_books(name=each['name'])
        else:
            list_of_books = get_books()

        for book in list_of_books:
            if (book[3] == 0):
                str = "FREE"
            else:
                str = "BORRROWED"
            print("Name: ", book[0], "owner:", book[2], "Status: ", str)


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
            print ("user_info exists: ", user_info.user_id, "with name", user_info.user_name, "shares with ", user_info.lendPref, "exchanges with ", user_info.exchangePref)
        else:
            print ("user_info does not exist: ", user_id)


    ###### borrowing related tests
    books = get_borrowable_books("haribcva@gmail.com")
    for book_url in books:
        print ("Book ", book_url[0], "is borrowable")
