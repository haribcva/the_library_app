-- Schema for to-do application examples.

-- Projects are high-level activities made up of tasks
create table db_books (
    book_name        varchar(256) NOT NULL,
    owner_email      varchar(256) NOT NULL,
    description      varchar(1024) NULL,
    status           integer(2) default 0,
    borrower_email   varchar(256) NULL,
    deadline         date NULL,
    primary key (book_name, owner_email)
    );
