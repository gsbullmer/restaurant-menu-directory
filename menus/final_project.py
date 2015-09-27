from flask import Flask, render_template, url_for, request, redirect, flash, jsonify
from sqlalchemy.sql import func

app = Flask(__name__)

# imports for CRUD Operations
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from database_setup import Restaurant, Base, MenuItem, User

# imports for OAuth
from flask import session as login_session
import random, string
from oauth2client.client import flow_from_clientsecrets, FlowExchangeError
import httplib2, json, requests
from flask import make_response

CLIENT_ID = json.loads(
    open('client_secrets.json', 'r').read())['web']['client_id']
APPLICATION_NAME = "Restaurant Menu Application"

# Create session and connect to DB
engine = create_engine('sqlite:///restaurantmenuwithusers.db')
Base.metadata.bind = engine
DBSession = sessionmaker(bind = engine)
session = DBSession()


@app.route('/')
@app.route('/restaurant/')
def showRestaurants():
    restaurants = session.query(Restaurant).order_by('name').all()

    if 'user_id' not in login_session:
        current_user = None
    else:
        current_user = getUserInfo(login_session['user_id'])

    return render_template("restaurants.html", restaurants = restaurants, current_user = current_user, getUserInfo = getUserInfo)

@app.route('/restaurant/new/', methods = ['GET', 'POST'])
def newRestaurant():
    if 'username' not in login_session:
        return redirect(url_for('showLogin'))
    if request.method == 'POST':
        newRestaurant = Restaurant(name = request.form['name'], user_id = login_session['user_id'])
        session.add(newRestaurant)
        session.commit()
        flash("New restaurant created")
        return redirect(url_for('showRestaurants'))
    else:
        return render_template("newRestaurant.html")

@app.route('/restaurant/<int:restaurant_id>/edit/', methods = ['GET', 'POST'])
def editRestaurant(restaurant_id):
    if 'username' not in login_session:
        return redirect(url_for('showLogin'))
    restaurant = session.query(Restaurant).filter_by(id = restaurant_id).one()
    if login_session['user_id'] != restaurant.user_id:
        flash("You don't have permission to edit that restaurant.")
        return redirect(url_for('showRestaurants'))
    if request.method == 'POST':
        restaurant.name = request.form['name']
        session.add(restaurant)
        session.commit()
        flash("Restaurant updated")
        return redirect(url_for('showRestaurants'))
    else:
        return render_template("editRestaurant.html", restaurant = restaurant)

@app.route('/restaurant/<int:restaurant_id>/delete/', methods = ['GET', 'POST'])
def deleteRestaurant(restaurant_id):
    if 'username' not in login_session:
        return redirect(url_for('showLogin'))
    restaurant = session.query(Restaurant).filter_by(id = restaurant_id).one()
    if login_session['user_id'] != restaurant.user_id:
        flash("You don't have permission to delete that restaurant.")
        return redirect(url_for('showRestaurants'))
    if request.method == 'POST':
        session.delete(restaurant)
        session.commit()
        flash("Restaurant deleted")
        return redirect(url_for('showRestaurants'))
    else:
        return render_template("deleteRestaurant.html", restaurant = restaurant)

@app.route('/restaurant/<int:restaurant_id>/')
@app.route('/restaurant/<int:restaurant_id>/menu/')
def showMenu(restaurant_id):
    restaurant = session.query(Restaurant).filter_by(id = restaurant_id).one()
    items = session.query(MenuItem).filter_by(restaurant_id = restaurant.id).order_by('name').all()

    courses = []
    for i in items:
        courses.append(i.course)

    courses = list(set(courses))
    courses.sort()

    if 'user_id' not in login_session:
        current_user = None
    else:
        current_user = getUserInfo(login_session['user_id'])

    return render_template("menu.html", restaurant = restaurant, items = items, courses = courses, current_user = current_user, getUserInfo = getUserInfo)

@app.route('/restaurant/<int:restaurant_id>/menu/new/', methods = ['GET', 'POST'])
def newMenuItem(restaurant_id):
    if 'username' not in login_session:
        return redirect(url_for('showLogin'))
    if request.method == 'POST':
        newItem = MenuItem(name = request.form['name'], price = request.form["price"], description = request.form["description"], course = request.form["course"], restaurant_id = restaurant_id, user_id = restaurant.user_id)
        session.add(newItem)
        session.commit()
        flash("New menu item created")
        return redirect(url_for('showMenu', restaurant_id = restaurant_id))
    else:
        return render_template("newMenuItem.html", restaurant_id = restaurant_id)

@app.route('/restaurant/<int:restaurant_id>/menu/<int:menu_id>/edit/', methods = ['GET', 'POST'])
def editMenuItem(restaurant_id, menu_id):
    if 'username' not in login_session:
        return redirect(url_for('showLogin'))
    item = session.query(MenuItem).filter_by(id = menu_id).one()
    if login_session['user_id'] != item.user_id :
        flash("You don't have permission to edit that menu item.")
        return redirect(url_for('showMenu', restaurant_id = restaurant_id))
    if request.method == "POST":
        if request.form["name"]:
            item.name = request.form["name"]

        if request.form["price"]:
            item.price = request.form["price"]

        if request.form["description"]:
            item.description = request.form["description"]

        if request.form["course"]:
            item.course = request.form["course"]

        session.add(item)
        session.commit()
        flash("Menu item updated")
        return redirect(url_for("showMenu", restaurant_id = restaurant_id))
    else:
        return render_template("editMenuItem.html", restaurant_id = restaurant_id, menu_id = menu_id, item = item)

@app.route('/restaurant/<int:restaurant_id>/menu/<int:menu_id>/delete/', methods = ['GET', 'POST'])
def deleteMenuItem(restaurant_id, menu_id):
    if 'username' not in login_session:
        return redirect(url_for('showLogin'))
    item = session.query(MenuItem).filter_by(id = menu_id).one()
    if login_session['user_id'] != item.user_id :
        flash("You don't have permission to delete that menu item.")
        return redirect(url_for('showMenu', restaurant_id = restaurant_id))
    if request.method == "POST":
        session.delete(item)
        session.commit()
        flash("Menu item deleted")
        return redirect(url_for("showMenu", restaurant_id = restaurant_id))
    else:
        return render_template("deleteMenuItem.html", restaurant_id = restaurant_id, item = item)


# Making an API Endpoint (GET Request)
@app.route('/restaurant/JSON')
def restaurantsJSON():
    restaurants = session.query(Restaurant).all()
    return jsonify(Restaurants = [r.serialize for r in restaurants])

@app.route('/restaurant/<int:restaurant_id>/menu/JSON')
def restaurantMenuJSON(restaurant_id):
    restaurant = session.query(Restaurant).filter_by(id = restaurant_id).one()
    items = session.query(MenuItem).filter_by(restaurant_id = restaurant.id).all()
    return jsonify(MenuItems = [i.serialize for i in items])

@app.route('/restaurant/<int:restaurant_id>/menu/<int:menu_id>/JSON')
def menuItemJSON(restaurant_id, menu_id):
    item = session.query(MenuItem).filter_by(id = menu_id).one()
    return jsonify(MenuItem = item.serialize)

@app.route('/login')
def showLogin():
    state = "".join(random.choice(string.ascii_uppercase + string.digits) for x in xrange(32))
    login_session['state'] = state
    return render_template("login.html", STATE = state)

@app.route('/gconnect', methods = ["POST"])
def gconnect():
    # Validate state token
    if request.args.get('state') != login_session['state']:
        response = make_response(json.dumps('Invalid state token'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Obtain authorization code
    code = request.data

    try:
        # Upgrade the authorization code into a credentials object
        oauth_flow = flow_from_clientsecrets('client_secrets.json',
            scope = '')
        oauth_flow.redirect_uri = 'postmessage'
        credentials = oauth_flow.step2_exchange(code)
    except FlowExchangeError:
        response = make_response(json.dumps('Failed to upgrade the authorization code.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Check that the access token is valid
    access_token = credentials.access_token
    url = ('https://www.googleapis.com/oauth2/v1/tokeninfo?access_token=%s' % access_token)
    h = httplib2.Http()
    result = json.loads(h.request(url, "GET")[1])

    # If there was an error in the access token info, abort
    if result.get('error') is not None:
        response = make_response(json.dumps(result.get('error')), 500)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Verify that the access token in used for the intended user
    gplus_id = credentials.id_token['sub']
    if result['user_id'] != gplus_id:
        response = make_response(json.dumps("Token's user ID doesn't match given user ID."), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Verify that the access token is valid for this app
    if result['issued_to'] != CLIENT_ID:
        response = make_response(json.dumps("Token's client ID doesn't match app's ID."), 401)
        print "Token's client ID doesn't match app's ID."
        response.headers['Content-Type'] = 'application/json'
        return response

    # Check to see if user is already logged in
    stored_credentials = login_session.get('credentials')
    stored_gplus_id = login_session.get('gplus_id')
    if stored_credentials is not None and gplus_id == stored_gplus_id:
        response = make_response(json.dumps("Current user is already connected"), 200)
        response.headers['Content-Type'] = 'application/json'
        # return response

    # Store the access token in the session for later use
    login_session['provider'] = 'google'
    login_session['credentials'] = credentials
    login_session['gplus_id'] = gplus_id

    # Get user info
    userinfo_url = "https://www.googleapis.com/oauth2/v1/userinfo"
    params = {'access_token': credentials.access_token, 'alt':'json'}
    answer = requests.get(userinfo_url, params = params)
    data = json.loads(answer.text)

    login_session['username'] = data["name"]
    login_session['picture'] = data["picture"]
    login_session['email'] = data["email"]

    user_id = getUserID(login_session['email'])
    if not user_id:
        user_id = createUser(login_session)
    login_session['user_id'] = user_id


    output = ''
    output += '<h1>Welcome, '
    output += login_session['username']
    output += '!</h1>'
    output += '<img src="'
    output += login_session['picture']
    output += ' " style = "width: 300px; height: 300px;border-radius: 150px;-webkit-border-radius: 150px;-moz-border-radius: 150px;"> '
    flash("you are now logged in as %s" % login_session['username'])
    print "done!"
    return output

# DISCONNECT - Revoke a current user's token and reset their login_session
@app.route('/gdisconnect')
def gdisconnect():
    # Only disconnect a connected user
    credentials = login_session.get('credentials')
    if credentials is None:
        response = make_response(
            json.dumps('Current user not connected.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    access_token = credentials.access_token
    url = 'https://accounts.google.com/o/oauth2/revoke?token=%s' % access_token
    h = httplib2.Http()
    result = h.request(url, 'GET')[0]

    if result['status'] == '200':
        response = make_response(json.dumps('Successfully disconnected.'), 200)
        response.headers['Content-Type'] = 'application/json'
        return response
    else:
        # For whatever reason, the given token was invalid
        response = make_response(
            json.dumps('Failed to revoke token for given user.', 400))
        response.headers['Content-Type'] = 'application/json'
        return response

@app.route('/fbconnect', methods=["POST"])
def fbconnect():
    if request.args.get('state') != login_session['state']:
        response = make_response(json.dumps("Invalid state parameter."), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    access_token = request.data

    app_id = json.loads(open('fb_client_secrets.json', 'r').read())['web']['app_id']
    app_secret = json.loads(open('fb_client_secrets.json', 'r').read())['web']['app_secret']
    url = 'https://graph.facebook.com/oauth/access_token?grant_type=fb_exchange_token&client_id=%s&client_secret=%s&fb_echange_token=%s' % (app_id, app_secret, access_token)
    h = httplib2.Http()
    result = h.request(url, "GET")[1]

    userinfo_url = "https://graph.facebook.com/v2.4/me"
    token = result.split("&")[0]

    url = 'https://graph.facebook.com/v2.4/me?%s&fields=name,id,email' % token

    h = httplib2.Http()
    result = h.request(url, "GET")[1]

    data = json.loads(result)
    login_session['provider'] = 'facebook'
    login_session['username'] = data["name"]
    login_session['email'] = data["email"]
    login_session['facebook_id'] = data["id"]

    url = 'https://graph.facebook.com/v2.4/me/picture?%s&redirect=0&height=200&width=200' % token
    h = httplib2.Http()
    result = h.request(url, "GET")[1]
    data = json.loads(result)
    login_session['picture'] = data["data"]["url"]

    user_id = getUserID(login_session['email'])
    if not user_id:
        user_id = createUser(login_session)
    login_session['user_id'] = user_id


    output = ''
    output += '<h1>Welcome, '
    output += login_session['username']
    output += '!</h1>'
    output += '<img src="'
    output += login_session['picture']
    output += ' " style = "width: 300; height: 300px;border-radius: 150px;-webkit-border-radius: 150px;-moz-border-radius: 150px;"> '
    flash("you are now logged in as %s" % login_session['username'])
    print "done!"
    return output

@app.route('/fbdisconnect')
def fbdisconnect():
    facebook_id = login_session['facebook_id']
    url = 'https://graph.facebook.com/%s/permissions' % facebook_id
    h = httplib2.Http()
    result = h.request(url, 'DELETE')[0]
    return "You have been logged out."

@app.route('/disconnect')
def disconnect():
    if 'provider' in login_session:
        if login_session['provider'] == 'google':
            gdisconnect()
            del login_session['gplus_id']
            del login_session['credentials']
        if login_session['provider'] == 'facebook':
            fbdisconnect()
            del login_session['facebook_id']

        del login_session['username']
        del login_session['email']
        del login_session['picture']
        del login_session['user_id']
        del login_session['provider']

        flash("You have successfully been logged out.")
        return redirect(url_for('showRestaurants'))
    else:
        flash("You were not logged in to begin with!")
        return redirect(url_for('showRestaurants'))

# User helper functions
def getUserID(email):
    try:
        user = session.query(User).filter_by(email = email).one()
        return user.id
    except:
        return None

def getUserInfo(user_id):
    user = session.query(User).filter_by(id = user_id).one()
    return user

def createUser(login_session):
    newUser = User(name = login_session['username'], email = login_session['email'], picture = login_session['picture'])
    session.add(newUser)
    session.commit()
    user = session.query(User).filter_by(email = login_session['email']).one()
    return user.id


if __name__ == '__main__':
    app.secret_key = 'super secret key'
    app.debug = True
    app.run(host = '0.0.0.0', port = 5000)
