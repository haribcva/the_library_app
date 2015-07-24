from flask import Flask
from flask import render_template, flash, redirect, make_response
from flask.ext.login import LoginManager
from flask.ext.openid import OpenID
import os, sys, logging
# from flask.ext.sqlalchemy import SQLAlchemy
from flask import render_template, flash, redirect, session, url_for, request, g
from flask.ext.login import login_user, logout_user, current_user, login_required

#gplus related
import json
import random
import string
from apiclient.discovery import build
from simplekv.memory import DictStore
from flaskext.kvsession import KVSessionExtension
from flask import send_file
import httplib2
from oauth2client.client import AccessTokenRefreshError
from oauth2client.client import flow_from_clientsecrets
from oauth2client.client import FlowExchangeError

#gplus related

WTF_CSRF_ENABLED = True
SECRET_KEY = 'you-will-never-guess'

OPENID_PROVIDERS = [
    {'name': 'Google', 'url': 'https://www.google.com/accounts/o8/id'},
    {'name': 'Yahoo', 'url': 'https://me.yahoo.com'},
    {'name': 'AOL', 'url': 'http://openid.aol.com/<username>'},
    {'name': 'Flickr', 'url': 'http://www.flickr.com/<username>'},
    {'name': 'MyOpenID', 'url': 'https://www.myopenid.com'}]

basedir = os.path.abspath(os.path.dirname(__file__))

print ("XXX", basedir)

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

#gplus related

# See the simplekv documentation for details
store = DictStore()

# This will replace the app's session handling
KVSessionExtension(store, app)

# Update client_secrets.json with your Google API project information.
# Do not change this assignment.
secrets_file_name = os.path.join(basedir, 'client_secrets.json')
CLIENT_ID = json.loads(
    open(secrets_file_name, 'r').read())['web']['client_id']
SERVICE = build('plus', 'v1')

#gplus related end

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

# can approve books one by one
# can approve all books in one shot
@app.route('/myapprovebooks', methods=['POST'])
def view_approve_books():
    user_id = session.get('login_email_addr', "guest")
    for key in request.values:
        print ("view_approve key  & values are:", key, request.values[key])
    if ("all" in request.values):
        #user is approving or rejecting all his requests.
        value = request.values.get("approve all", None)
        if (value == None):
            approve_books(user_id, "reject")
        else:
            approve_books(user_id, "approve")
    else:
        # user is approving specific book; key will be of format 'approveMANGLED_BOOKNAME' format
        magic_format_len = len("approve")
        for key in request.values:
            # use string slicing to locate start of mangled bookname
            mangled_bookname = key[magic_format_len:]

            approve_books(user_id, request.values[key],mangled_bookname)

    #at this time send him back to home page; the home page should have links
    #to approve more books or none if all books have been approved.
    return redirect('/index')

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
#@app.route('/fake_login', methods=['GET'])
#def fake_login():
#    email = request.args.get('email', 'haribcva@gmail.com')
#    f1 = FakeResp(email)
#    return (after_login(f1))
    #return redirect('/index')

@app.route('/fakelogin', methods=['GET', 'POST'])
def fake_login():
    if request.method == 'POST':
        email = request.values.get("email",None)
        f1 = FakeResp(email)
        #it will redirect to home page finally.
        return (after_login(f1))
    else:
        return render_template("fake_login.html")

@app.route('/login', methods=['GET', 'POST'])
#@oid.loginhandler
def login():
    # if g.user is not None and g.user.is_authenticated():
    #    return redirect(url_for('index'))

    cookie_val = 'guest'
    not_logged = True

    is_logout = request.args.get('logout_button', None)
    if (is_logout):
        session.pop('login_email_addr')
        g.user = None
        session['logged in'] = False
        # must redirect to home page
        return redirect('/index')

    is_gplus_login = request.args.get('gplus_login_button', None)
    if (is_gplus_login):
        # use gmail login logo and processing...
        return redirect('/login2')

    is_fake_login = request.args.get('fake_login_button', None)
    if (is_fake_login):
        # render fake login form 
        return redirect('/fakelogin')

    # neither login or logout, user directly entered into "/login" url 
    return redirect('/index')

#@oid.after_login
def after_login(resp):
    #print ("in after_login step", resp.email)

    if resp.email is None or resp.email == "":
        flash('Invalid login. Please try again.')
        print ("invalid login seen")
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
    print "to add user, redirecting to index page post login", resp.email, nickname
    add_user(resp.email, nickname)
    return redirect('/index')
    #return redirect(request.args.get('next') or url_for('index'))

#gplus related
APPLICATION_NAME = 'Google+ Python Quickstart'

@app.route('/login2', methods=['GET'])
def gplus_login():
  print ("in login2")
  """Initialize a session for the current user, and render index.html."""
  # Create a state token to prevent request forgery.
  # Store it in the session for later validation.
  state = ''.join(random.choice(string.ascii_uppercase + string.digits)
                  for x in xrange(32))
  session['state'] = state
  # Set the Client ID, Token State, and Application Name in the HTML while
  # serving it.
  response = make_response(
      render_template('login_gplus.html',
                      CLIENT_ID=CLIENT_ID,
                      STATE=state,
                      APPLICATION_NAME=APPLICATION_NAME))
  response.headers['Content-Type'] = 'text/html'
  return response

@app.route('/signin_button.png', methods=['GET'])
def signin_button():
  """Returns the button image for sign-in."""
  return send_file("templates/gplus_button.png", mimetype='image/gif')

@app.route('/connect', methods=['POST'])
def connect():
  """Exchange the one-time authorization code for a token and
  store the token in the session."""
  print ("in gplus connect...")
  # Ensure that the request is not a forgery and that the user sending
  # this connect request is the expected user.
  if request.args.get('state', '') != session['state']:
    response = make_response(json.dumps('Invalid state parameter.'), 403)
    response.headers['Content-Type'] = 'application/json'
    print ("in gplus connect...not connected")
    return response
  # Normally, the state is a one-time token; however, in this example,
  # we want the user to be able to connect and disconnect
  # without reloading the page.  Thus, for demonstration, we don't
  # implement this best practice.
  # del session['state']

  code = request.data

  try:
    # Upgrade the authorization code into a credentials object
    oauth_flow = flow_from_clientsecrets('client_secrets.json', scope='https://www.googleapis.com/auth/plus.login https://www.googleapis.com/auth/plus.profile.emails.read')
    oauth_flow.redirect_uri = 'postmessage'
    credentials = oauth_flow.step2_exchange(code)
  except FlowExchangeError:
    response = make_response(
        json.dumps('Failed to upgrade the authorization code.'), 404)
    response.headers['Content-Type'] = 'application/json'
    print ("in gplus connect...failed to upgrade auth code")
    return response

  # An ID Token is a cryptographically-signed JSON object encoded in base 64.
  # Normally, it is critical that you validate an ID Token before you use it,
  # but since you are communicating directly with Google over an
  # intermediary-free HTTPS channel and using your Client Secret to
  # authenticate yourself to Google, you can be confident that the token you
  # receive really comes from Google and is valid. If your server passes the
  # ID Token to other components of your app, it is extremely important that
  # the other components validate the token before using it.
  gplus_id = credentials.id_token['sub']

  stored_credentials = session.get('credentials')
  stored_gplus_id = session.get('gplus_id')
  if stored_credentials is not None and gplus_id == stored_gplus_id:
    response = make_response(json.dumps('Current user is already connected.'),
                             200)
    response.headers['Content-Type'] = 'application/json'
    print ("in gplus connect...user already connected")
    return response
  # Store the access token in the session for later use.
  session['credentials'] = credentials
  session['gplus_id'] = gplus_id
  response = make_response(json.dumps('Successfully connected user.', 200))
  response.headers['Content-Type'] = 'application/json'
  print ("in gplus connect...user now connected")
  return response


@app.route('/disconnect', methods=['POST'])
def disconnect():
  """Revoke current user's token and reset their session."""

  # Only disconnect a connected user.
  print ("in gplus disconnect...")
  credentials = session.get('credentials')
  if credentials is None:
    response = make_response(json.dumps('Current user not connected.'), 401)
    response.headers['Content-Type'] = 'application/json'
    return response

  # Execute HTTP GET request to revoke current token.
  access_token = credentials.access_token
  url = 'https://accounts.google.com/o/oauth2/revoke?token=%s' % access_token
  h = httplib2.Http()
  result = h.request(url, 'GET')[0]

  if result['status'] == '200':
    # Reset the user's session.
    del session['credentials']
    response = make_response(json.dumps('Successfully disconnected.'), 200)
    response.headers['Content-Type'] = 'application/json'
    print ("in gplus disconnect...user disconnected now")
    return response
  else:
    # For whatever reason, the given token was invalid.
    response = make_response(
        json.dumps('Failed to revoke token for given user.', 400))
    response.headers['Content-Type'] = 'application/json'
    print ("in gplus disconnect...error in revoking token")
    return response

@app.route('/people', methods=['GET'])
def people():
  """Get list of people user has shared with this app."""
  print ("in gplus people...")
  credentials = session.get('credentials')
  # Only fetch a list of people for connected users.
  if credentials is None:
    response = make_response(json.dumps('Current user not connected.'), 401)
    response.headers['Content-Type'] = 'application/json'
    print ("in gplus people...user not connected")
    return response
  try:
    # Create a new authorized API client.
    http = httplib2.Http()
    http = credentials.authorize(http)
    # Get a list of people that this user has shared with this app.
    google_request = SERVICE.people().list(userId='me', collection='visible')
    list_result = google_request.execute(http=http)
    # n = list_result.get('totalItems')
    # loop over "n"
    # id = list_result.get('items')[i].get('id')
    # execute get request on "id"
    #form a session variable "gplus_email_list" to form the list of
    # email addresses that this user has chosen to be made visible to
    # this app. Not all id will give the email addr as some of those
    # folks would not have logged into our app, but that is ok.
    # those users who have not logged in don't have any books to
    # contribute and knowing their infornation is not useful,

    # first add this user to our database
    google_request = SERVICE.people().get(userId='me')
    get_result = google_request.execute(http=http)
    # get_dumps = json.dumps(get_result)
    dispName = get_result.get('displayName')
    # check this....
    gplus_id = get_result.get('uid')
    email = get_result.get('emails')[0].get('value')
    session['login_email_addr'] = email
    session['logged in'] = True

    ### need to store the gplus ID in the database. Need to introduce facebook ID too in the user database.
    add_user(email, dispName, gplus_id=gplus_id)

    # now go over all the ids this user has chosen to expose to this app
    # there is no way to get the email of the person not currently logged in.
    # instead when a person logs in we need to get their email and store the 
    # id & email in the database. [NOT NEEDED: We need to go over the ids that this person
    # has in his contact (or filtered by some circles such as lending-book-circle)
    # and lookup each id in the database to get the email.)
    # this way we can form the (this_userid->email_lists_of_friends_in_group)]
    # note that when user logs in via gmail-id, we can still get his facebook-id
    # by looking in the database. The facebook id can be gotten when a user
    # logins via FB for first time. Since we can get email-id of logged-in person
    # from FB too, the key of the UserDB can be the email-id. Thus has a person
    # ever logged via FB or Gmail to the app, we can get the FB or GP ids.
    # If a book owner has decided to share his book via contacts in FB or GP
    # we need to see if the current logged in user belongs to either of the group.
    # I hope that given a FB id (and prior offline permissions), it 
    # would be possible to fetch the contacts for that id. If so, when we hit a 
    # book whose owner wants to share with FB group, we can lookup our DB to get the
    # FB Id of the owner. Then we can lookup FB with that ID and determine IDs of the
    # owner's group members. If our logged in user's FB Id is in this list, then
    # this is a borrowable book. This assumes that any user must alteast login once
    # via GP and FB, if the user has accounts in both places. There must be atleast
    # one intersection between lender's circle and current logged in person's circle
    # if the lender has not make his lending pref as "ALL". With this, we need not
    # form the (userid->email_list_of_friends_in_circles).
 
    session['gplus_known_users'] = []
    list_count = list_result.get('totalItems')
    for i in range(0, list_count):
        id = list_result.get('items')[i].get('id')
        google_request = SERVICE.people().get(userId=id)
        get_result = google_request.execute(http=http)
        email_arr = get_result.get('emails')
        if (email_arr is None):
            continue
        email = email_arr[0].get('value')
        if (email is None):
            continue
        session['gplus_known_users'].append(email)

    # must redirect to the page which collects the lending & exchange preference
    # all this info will be used to add the user to the database and redirect
    # the user to the page after login.
    print("for user:", dispName, "known folks are:", session['gplus_known_users'])
    return redirect('/index')
    #response = make_response(json.dumps(list_result), 200)
    #response.headers['Content-Type'] = 'application/json'


    #return response
  except AccessTokenRefreshError:
    #response = make_response(json.dumps('Failed to refresh access token.'), 500)
    #response.headers['Content-Type'] = 'application/json'
    #return response

    #Need to generate error html code....
    print("AccessTokenRefreshError for id:", id)
    return redirect('/index')

#end gplus related


#@login_required
######### End Login related
@app.route('/', methods=['GET', 'POST'])
@app.route('/index', methods=['GET', 'POST'])
def index():
    user = {'nickname': 'guest'}  # fake user
    borrowed_books = {}
    pending_books  = {}
    approve_books  = {}
    not_logged = True

    logged_in = session.get('logged in', False)
    if (logged_in == True):
        user_id = session.get('login_email_addr', "guest")
        print ("logged in set, email addr is", user_id)
        nickname = user_id.split('@')[0]
        user = {'nickname': nickname}
        borrowed_books, pending_books, approve_books  = user_get_data(user_id)
        #print "got borrowed_books as:",
        #print user_borrowed_books
        not_logged = False
    else:
        ## ensure the session always has this key as template code relies on this
        ## field being present
        session['logged in'] = False


    # convoluted logic is due to how base.html is strcutured. It is assumed that every
    # page other than index can be reached only if login attempt has succeeded.
    # not_logged  would be made available only from index.html, though the base.html
    # which has the login/logout button show logic is used by every template file.
    resp = make_response(render_template("index.html",
                           title='Home',
                           user=user,
                           not_logged=not_logged,
                           borrowed_books=borrowed_books,
                           pending_books=pending_books,
                           approve_books=approve_books))
    return resp

#initDatabase(basedir)
#initEmailSubsystem()
init_library_system(basedir)

if __name__ == '__main__':
    #app.run()
    app.run(host='0.0.0.0', port=4567)
