from flask import Flask
from flask import render_template, flash, redirect, make_response
from flask.ext.login import LoginManager
from flask.ext.openid import OpenID
import os, sys, logging
# from flask.ext.sqlalchemy import SQLAlchemy
from flask import render_template, flash, redirect, session, url_for, request, g
from flask.ext.login import login_user, logout_user, current_user, login_required

WTF_CSRF_ENABLED = True
SECRET_KEY = 'you-will-never-guess'

OPENID_PROVIDERS = [
    {'name': 'Google', 'url': 'https://www.google.com/accounts/o8/id'},
    {'name': 'Yahoo', 'url': 'https://me.yahoo.com'},
    {'name': 'AOL', 'url': 'http://openid.aol.com/<username>'},
    {'name': 'Flickr', 'url': 'http://www.flickr.com/<username>'},
    {'name': 'MyOpenID', 'url': 'https://www.myopenid.com'}]

basedir = os.path.abspath(os.path.dirname(__file__))

SQLALCHEMY_DATABASE_URI = 'sqlite:///' + os.path.join(basedir, 'app.db')
SQLALCHEMY_MIGRATE_REPO = os.path.join(basedir, 'db_repository')

def initLogging():
    path = os.path.join(basedir, "log", "library_log")
    logHandler = logging.FileHandler(path)
    logHandler.setLevel(logging.INFO)
    logHandler.setFormatter(logging.Formatter(
            '%(asctime)s %(levelname)s: %(message)s '
                '[in %(pathname)s:%(lineno)d]'
                ))
    app.logger.addHandler(logHandler)

app = Flask(__name__)
app.config.from_object('config')
initLogging()
app.logger.warning("to init Login Manager subsystem")
lm = LoginManager()
lm.init_app(app)
oid = OpenID(app, os.path.join(basedir, 'tmp'))

from flask.ext.wtf import Form
from wtforms import StringField, BooleanField
from wtforms.validators import DataRequired

class PostForm(Form):
    post = StringField('post', validators=[DataRequired()])
    book = StringField('book', validators=[DataRequired()])


from dbmodel import *
from library import *

@app.route('/style.css', methods=['GET'])
def get_style_css():
    return render_template("style.css")

@app.route('/app.js', methods=['GET'])
def get_app_js():
    return render_template("app.js")

@app.route('/donate_books', methods=['GET', 'POST'])
def donate_books():
    if request.method == 'POST':
        book = request.values["bookname"]
        str = "Thanks a bunch for donating " + book
        flash (str)
        return redirect('/mybooks')
    return render_template("donate_books.html")

@app.route('/exchange_books', methods=['GET', 'POST'])
def exchange_books():
    if request.method == 'POST':
        choice = request.values['choice_of_group']
        if (choice.find("All") != -1):
            flash ("You have chosen to exchange books with everyone")
        else:
            flash ("You are exchanging books only with select group")
        return redirect('/mybooks')
    return render_template("exchange_books.html")

@app.route('/lend_books', methods=['GET', 'POST'])
def lend_books():
    if request.method == 'POST':
        choiceDict = request.values
        for key in choiceDict:
            add_book(choiceDict[key], session.get('login_email_addr','haribcva@gmail.com'))

        return redirect('/mybooks')
    return render_template("lend_books.html")

@app.route('/borrow', methods=['GET', 'POST'])
def borrow_books():
    books=[]
    if request.method == 'POST':
        if (request.form["bookname"] == ""):
            ### user is asking to show all books that he can borrow
            books = get_borrowable_books(session.get('login_email_addr','haribcva@gmail.com'))
            #to allow for scripts not using sessions, don't depend on session for now
        else:
            ### user is performing a search with specific bookname.
            books = regex_search_borrowable_books(session.get('login_email_addr','haribcva@gmail.com'), request.form["bookname"])

    return render_template("my_books.html",
                           title='Books you can borrow',
                           your_books=books)

@app.route('/borrowthis', methods=['GET'])
def borrow_book_byname():
    bookname = request.args.get('name', '')
    owner = request.args.get('owner', '')
    #print "Attempting to borrow", bookname, owner
    borrower = session.get('login_email_addr',u'chitrakris@gmail.com');
    message = "message default"
    status,message = borrow_this_book(bookname, owner, borrower)
    if (not status):
        return render_template('error.html', msg=message), 403
    else:
        return render_template('success.html', msg=message), 200

@app.route('/what_work', methods=['GET', 'POST'])
def get_whatwork():
    if request.method == 'POST':
        try:
            for key in request.form:
                break
            key = "/" + key
            return redirect(key)
        except:
            flash ("Exception happened")
            return redirect('/mybooks')
    else:
        return redirect('/my_books_xxx')
    return redirect('/index')


@app.route('/mybooks', methods=['GET', 'POST'], defaults={'path': ''})
@app.route('/mybooks/<path:path>')
def get_mybooks(path):
    # /mybooks/"bookname" should get that book; path == "bookname" in this case
    # /mybooks/app.js and /mybooks/style.css should be ignored.
    # only /mybooks/ should get all books; path == "" in this case
    books=[]
    detailed = False
    if (path == ''):
        books = get_books()
    elif (path.find("@") != -1):
        books = get_books(user=path)
    else:
        detailed = True
        books = get_books(name=path)
    #print "returned books were", books
    if (detailed == False):
        return render_template("my_books.html",
                           title='My Books',
                           your_books=books)
    else:
        return render_template("books_detailed.html",
                           title='My Books',
                           your_books=books)

##### Login Related Starts from here

lm = LoginManager()
lm.init_app(app)
lm.login_view = 'login'

@lm.user_loader
def load_user(id):
    return 100

class LoginForm(Form):
    openid = StringField('openid', validators=[DataRequired()])
    remember_me = BooleanField('remember_me', default=False)


#before every request is processed, this function is called; it can be used to clear
#per request variables. "g" should be used to communicate data in the context of
#current request from the view function that handled the request. Passing args explicitly
#is one way, but when redirect_url is done, passing args is not possible and
#"g" is used as a place to dump information between functions that will be valid only
#in the context of current request.
@app.before_request
def before_request():
    g.user = current_user

class FakeResp(object):
    def __init__(self, email):
        self.email = email

# we need this as a way to add users to database
#/fake_login?email=....
@app.route('/fake_login', methods=['GET'])
def fake_login():
    email = request.args.get('email', 'haribcva@gmail.com')
    f1 = FakeResp(email)
    return (after_login(f1))
    #return redirect('/index')

@app.route('/login', methods=['GET', 'POST'])
#@oid.loginhandler
def login():
    # if g.user is not None and g.user.is_authenticated():
    #    return redirect(url_for('index'))

    #if 'logged in' in session:
    #    print ("user had already logged in")
    #    app.logger.info("user name {0} has already logged in.".format(session.get('login_email_addr', "guest")))
    #    return redirect('/index')

    cookie_val = 'guest'
    not_logged = True

    is_logout = request.args.get('logout_button', None)
    if (is_logout):
        session.pop('login_email_addr')
        g.user = None
        session['logged in'] = False
        # must redirect to home page
        return redirect('/index')

    is_login = request.args.get('login_button', None)
    if (is_login):
        logged_in = session.get('logged in', False)
        if logged_in:
            #print ("user had already logged in")
            app.logger.info("user name {0} has already logged in.".format(session.get('login_email_addr', "guest")))
            return redirect('/index')

        app.logger.info("user name {0} is now logged in.".format(session.get('login_email_addr', "guest")))
        # for now allow all logins without actual verification
        not_logged = False
        cookie_val = session.get('login_email_addr', "haribcva@gmail.com")

        # this will redirect to index page.
        return(fake_login())
    else:
        # neither login or logout, user directly entered into "/login" url 
        return redirect('/index')

    #user = {'nickname': cookie_val}
    #resp = make_response(render_template('index.html',
    #                       title='Home',
    #                       user=user,
    #                       not_logged=not_logged,
    #                       borrowed_books=[]))
    # cookie stuff is really not needed for login processing, added here just to see how to set cookies
    #resp.set_cookie('username', cookie_val)
    #return (resp)

    #form = LoginForm()
    #if form.validate_on_submit():
    #    print ("in driving logic of core login")
    #    session['remember_me'] = form.remember_me.data
    #    return oid.try_login(form.openid.data, ask_for=['nickname', 'email'])

    #return render_template('login.html',
    #                       title='Sign In',
    #                       form=form,
    #                       providers=OPENID_PROVIDERS)

#@oid.after_login
def after_login(resp):
    #print ("in after_login step", resp.email)

    if resp.email is None or resp.email == "":
        flash('Invalid login. Please try again.')
        print "invalid login seen"
        return redirect(url_for('login'))
    # user = User.query.filter_by(email=resp.email).first()
    session['login_email_addr'] = resp.email
    nickname = resp.email.split('@')[0]
    remember_me = False
    if 'remember_me' in session:
        remember_me = session['remember_me']
        session.pop('remember_me', None)
    # login_user(user, remember = remember_me)
    session['logged in'] = True
    add_user(resp.email, nickname)
    #print "added user, redirecting to index page post login", resp.email, nickname
    return redirect('/index')
    #return redirect(request.args.get('next') or url_for('index'))

#@login_required
######### End Login related
@app.route('/', methods=['GET', 'POST'])
@app.route('/index', methods=['GET', 'POST'])
def index():
    user = {'nickname': 'guest'}  # fake user
    user_borrowed_books = {}

    try:
        if (session['logged in'] == True):
            print "logged in set, email addr is", session.get('login_email_addr', "XXX")
            nickname = session['login_email_addr'].split('@')[0]
            user = {'nickname': nickname}
            user_borrowed_books = borrow_get_borrower_data(session['login_email_addr'])
            #print "got borrowed_books as:",
            #print user_borrowed_books
    except:
        # login did not happen well, add hari as default user.
        session['login_email_addr'] = "haribcva@gmail.com"
        pass


    # convoluted logic is due to how base.html is strcutured. It is assumed that every
    # page other than index can be reached only if login attempt has succeeded.
    # not_logged  would be made available only from index.html, though the base.html
    # which has the login/logout button show logic is used by every template file.
    not_logged = True
    logged_in = session.get('logged in', False)
    if (logged_in == True):
        not_logged = False

    resp = make_response(render_template("index.html",
                           title='Home',
                           user=user,
                           not_logged=not_logged,
                           borrowed_books=user_borrowed_books))
    return resp

initDatabase(basedir)
initEmailSubsystem()

if __name__ == '__main__':
    app.run()
