STATUS_FREE     = 0
STATUS_BORROWED = 1
STATUS_RESERVED = 2

class bookData:
    def __init__(self, owner_email):
        self.owner = owner_email
        self.status = STATUS_FREE
        # who has borrowed this book and related info (due date etc)
        self.borrowerData = None
        # other data that can be added are isbn code

class userData:
    def __init__(self, user_email, user_name, lendPref, exchangePref):
        self.user_id = user_email
        self.user_name = user_name
        self.updateUserData(lendPref, exchangePref)
        # all of the following data needs to be made consistent of form [(bookname, user_id)]
        #a list of books that this person has borrowed
        self.borrowedBooks = []
        # a list of books that this person has reserved ie books pending approval by owner of that book
        self.reservedBooks = []
        # a list of tuples of form (bookname, borrower_id): identifies list of books that needs to be approved for lending
        self.approveBooks = []
        #list of tuples of form (bookname, borrower_id): identifies list of books that has been lent
        self.lentBooks = []

    def updateUserData(self, lendPref, exchangePref):
        # all, friends only ("google+" or "facebook")
        self.lendPref = None
        if lendPref in ["All", "google+", "facebook"]:
            self.lendPref = lendPref
        self.exchangePref = None
        if exchangePref in ["All", "google+", "facebook"]:
            self.exchangePref = exchangePref
