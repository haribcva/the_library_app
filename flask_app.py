from flask import Flask
from flask import render_template, flash, redirect
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
    logHandler.setLevel(logging.WARNING)
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
databaseInited = False

from flask.ext.wtf import Form
from wtforms import StringField, BooleanField
from wtforms.validators import DataRequired

class PostForm(Form):
    post = StringField('post', validators=[DataRequired()])
    book = StringField('book', validators=[DataRequired()])

class bookData:
    def __init__(self, owner_email):
        self.owner = owner_email
        self.status = STATUS_FREE
        self.borrowerData = None

class userData:
    def __init__(self, user_email, user_name, lendPref, exchangePref):
        self.user_id = user_email
        self.user_name = user_name
        self.updateUserData(lendPref, exchangePref)

    def updateUserData(self, lendPref, exchangePref):
        # all, friends only ("google+" or "facebook")
        self.lendPref = None
        if lendPref in ["All", "google+", "facebook"]:
            self.lendPref = lendPref
        self.exchangePref = None
        if exchangePref in ["All", "google+", "facebook"]:
            self.exchangePref = exchangePref

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
            add_book(choiceDict[key], session['login_email_addr'])

        return redirect('/mybooks')
    return render_template("lend_books.html")

@app.route('/borrow', methods=['GET', 'POST'])
def borrow_books():
    books=[]
    if request.method == 'POST':
        if (request.form["bookname"] == ""):
            ### user is asking to show all books that he can borrow
            #books = get_borrowable_books(session['login_email_addr'])
            books = get_borrowable_books('chitrakris@gmail.com')
        else:
            ### user is performing a search with specific bookname.
            books = regex_search_borrowable_books(session['login_email_addr'], request.form["bookname"])

    return render_template("my_books.html",
                           title='Books you can borrow',
                           your_books=books)


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
    if (path == ''):
        books = get_books()
    elif (path.find("@") != -1):
        books = get_books(user=path)
    else:
        books = get_books(name=path)
    print "returned books were", books
    return render_template("my_books.html",
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
    global databaseInited, basedir
    if (databaseInited == False):
        initDatabase(basedir)
        databaseInited = True

@app.route('/login', methods=['GET', 'POST'])
@oid.loginhandler
def login():
    if request.method == 'POST':
        print ("in login via POST")
    else:
        print ("in login via GET")

    # if g.user is not None and g.user.is_authenticated():
    #    return redirect(url_for('index'))

    if 'logged in' in session:
        print ("user had already logged in")
        return redirect('/index')

    form = LoginForm()
    if form.validate_on_submit():
        print ("in driving logic of core login")
        session['remember_me'] = form.remember_me.data
        return oid.try_login(form.openid.data, ask_for=['nickname', 'email'])

    return render_template('login.html',
                           title='Sign In',
                           form=form,
                           providers=OPENID_PROVIDERS)

@oid.after_login
def after_login(resp):
    print ("in after_login step")

    if resp.email is None or resp.email == "":
        flash('Invalid login. Please try again.')
        print "invalid login seen"
        return redirect(url_for('login'))
    # user = User.query.filter_by(email=resp.email).first()
    flash('got email as ' + resp.email)
    session['login_email_addr'] = resp.email
    nickname = resp.email.split('@')[0]
    flash("hello " + nickname + " !!")
    remember_me = False
    if 'remember_me' in session:
        remember_me = session['remember_me']
        session.pop('remember_me', None)
    # login_user(user, remember = remember_me)
    session['logged in'] = True
    return redirect('/index')
    # return redirect(request.args.get('next') or url_for('index'))

#@login_required
######### End Login related
@app.route('/', methods=['GET', 'POST'])
@app.route('/index', methods=['GET', 'POST'])
def index():

    user = {'nickname': 'guest'}  # fake user
    user_borrowed_books = {}

    try:
        if (session['logged in'] == True):
            nickname = session['login_email_addr'].split('@')[0]
            user = {'nickname': nickname}
            user_borrowed_books = get_borrowed_books(session['login_email_addr'])
    except:
        # login did not happen well, add hari as default user.
        session['login_email_addr'] = "haribcva@gmail.com"
        pass


    return render_template("index.html",
                           title='Home',
                           user=user,
                           borrowed_books=user_borrowed_books)

if __name__ == '__main__':
    app.run()
