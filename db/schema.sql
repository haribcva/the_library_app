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

create table db_users (
    user_email         varchar(256) NOT NULL primary key,
    user_name          varchar(256) NOT NULL,
    lend_pref          integer default 0,
    exchange_pref      integer default 0,
    count_borrowed     integer default 0,
    count_pending      integer default 0,
    gplus_id           integer default 0,
    facebk_id         integer default 0
    );
