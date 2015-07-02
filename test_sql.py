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

import os
import sqlite3
import code

db_filename = 'books.db' 
schema_filename = 'schema.sql'

def create_book_table():
    db_is_new = not os.path.exists(db_filename) 
    conn = sqlite3.connect(db_filename)

    if db_is_new:
        print 'Need to create schema'
        with open(schema_filename, 'rt') as f:
            schema = f.read()
        conn.executescript(schema)
        print 'Database opened, schema run.'
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

    print "all books added" 

def close_db(conn):
    conn.close()

def show_all_books(conn):
    cursor = conn.cursor()
    cursor.execute("""
    select * from db_books
    """)

    print ("data from table is: ")
    for row in cursor.fetchall():
        print (row)

    return (row)

def is_book_present(conn, name, owner):
    cursor = conn.cursor()

    #cursor.execute("""
    #select * from db_books where book_name = ?
    #""", (name,))

    cursor.execute("""
    select * from db_books where book_name = :book AND owner_email = :email
    """, {'book': name, 'email': owner})

    print ("before fetchall, showing column info")
    for colinfo in cursor.description:
        print colinfo

    answer = cursor.fetchall()
   
    print ("is_book_present:", type(answer))

    for book in answer:
        print book

    print ("after fetchall, showing column info")
    for colinfo in cursor.description:
        print colinfo

    if (len(answer) == 0):
        return (False)
    else:
        return (True)


def add_books_dynamic(conn, value):
    # value must be a tuple of rows in right order
    # we must know the number of tuple elements so we can unpack cleanly

    cursor = conn.cursor()

    cursor.execute("""
       insert into db_books (book_name, owner_email) values (?, ?)
    """, value)

    # explicit commit
    conn.commit()

if (__name__ == "__main__"):
    conn = create_book_table()

    add_some_books(conn)
    value = ("SQL programming", "haribcva@gmail.com")
    add_books_dynamic(conn, value)

    row = show_all_books(conn)

    if (is_book_present(conn, "Harry Potter", "chitrakris@gmail.com") is True):
        print ("Book found")
    else:
        print ("Book not found")

    conn.row_factory = sqlite3.Row
    print "After changing row_factory...."
    row = show_all_books(conn)

    print "testing Row Factory.... name is: ", row['book_name'], row['owner_email']
    code.interact(local=globals())

    close_db(conn)
