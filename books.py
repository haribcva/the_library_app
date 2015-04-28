from flask import Flask
from flask import render_template, flash, redirect
from flask.ext.login import LoginManager
from flask.ext.openid import OpenID
import os, sys
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


app = Flask(__name__)
app.config.from_object('config')
lm = LoginManager()
lm.init_app(app)
oid = OpenID(app, os.path.join(basedir, 'tmp'))

from flask.ext.wtf import Form
from wtforms import StringField, BooleanField
from wtforms.validators import DataRequired

lm = LoginManager()
lm.init_app(app)
lm.login_view = 'login'

def handleBook(book,user="default"):
    print (book)

@lm.user_loader
def load_user(id):
    return 100

class LoginForm(Form):
    openid = StringField('openid', validators=[DataRequired()])
    remember_me = BooleanField('remember_me', default=False)

@app.before_request
def before_request():
    g.user = current_user

@app.route('/login', methods=['GET', 'POST'])
@oid.loginhandler
def login():
    flash("to login now")
    # flash(g.user())
    # if g.user is not None and g.user.is_authenticated():
    #    return redirect(url_for('index'))
    if 'logged in' in session:
        flash("logged in done for this session")
        return redirect('/index')
    form = LoginForm()
    if form.validate_on_submit():
        session['remember_me'] = form.remember_me.data
        return oid.try_login(form.openid.data, ask_for=['nickname', 'email'])
        # return redirect('/index')
    return render_template('login.html',
                           title='Sign In',
                           form=form,
                           providers=OPENID_PROVIDERS)

@oid.after_login
def after_login(resp):
    if resp.email is None or resp.email == "":
        flash('Invalid login. Please try again.')
        return redirect(url_for('login'))
    # user = User.query.filter_by(email=resp.email).first()
    flash('got email as ' + resp.email)
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

class PostForm(Form):
    post = StringField('post', validators=[DataRequired()])
    book = StringField('book', validators=[DataRequired()])

def add_book_to_database(bookname, user_name):
    # write to a file
    try:
         line = bookname + ":" + user_name
         outFile = open('output.txt', mode='w')
         outFile.write(line)
    except:
        pass

    outFile.close()

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
            handleBook(choiceDict[key], g.user())

        return redirect('/mybooks')
    return render_template("lend_books.html")

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


@app.route('/mybooks', methods=['GET', 'POST'])
def get_mybooks():
    flash ("to get all your books")
    books = [("Harry Potter","http://en.wikipedia.org/wiki/Harry_Potter"),
             ("Bhagvad Gita", "http://en.wikipedia.org/wiki/Harry_Potter"),
             ("Learn HTM5", "http://en.wikipedia.org/wiki/Harry_Potter")]
    return render_template("my_books.html",
                           title='My Books',
                            your_books=books)

# @login_required
@app.route('/', methods=['GET', 'POST'])
@app.route('/index', methods=['GET', 'POST'])
def index():
    # myfunc()
    # return myfunc()

    user = {'nickname': 'Miguel'}  # fake user
    # user = g.user()
    # flash("after logging got user as: " + g.user())

    posts = [  # fake array of posts
        {
            'author': {'nickname': 'John'},
            'body': 'Beautiful day in Portland!'
        },
        {
            'author': {'nickname': 'Susan'},
            'body': 'The Avengers movie was so cool!'
        }
    ]
    form = PostForm()
    if form.is_submitted():
    # if form.validate_on_submit():
    # if request.method == 'POST':
        # flash ("form submitted")

        post = form.post.data
        book = form.book.data
        book_string = str(book)
        add_book_to_database(book_string, "hari")
        flash('Your book data is received')

        return redirect('/login')
    else:
        # flash("no post for you")
        a = None

    # flash(form)
    # flash("XXX")
    return render_template("index.html",
                           title='Home',
                           user=user,
                           form=form,
                           posts=posts)

if __name__ == '__main__':
    sys.path.extend(['C:\\Users\\haribala\\PycharmProjects\\helloWorld'])
    app.run()
