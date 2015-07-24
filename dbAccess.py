DB_SQL = 1

class appDatabase(object):
    """ base class for the storage of books; it is expected that derived classes
    will be built on top of it implementing multiple approaches."""
    def __init__(self, type=DB_SQL):
        self.type = type

    def dbAccess_closeDb(self):
        self.type = None

    def dbAccess_isUserPresent(self, email_id):
        raise(NotImplementedError("subclass db should implement it"))

def initDatabase(path, type=DB_SQL):
    print ("MMMMM... in initDatabase")
    if (type == DB_SQL):
         from dbAccess_sql import appDatabaseSql
         print ("MMMMM... in initDatabase SQL")
         db = appDatabaseSql(path)
         return (db)
    else:
     # assume shelve
         from dbAccess_shelve import appDatabaseShelve
         print ("MMMMM... in initDatabase Shelve")
         return (appDatabaseShelve(path))
