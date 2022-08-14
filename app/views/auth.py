"""
View responsible for authentication-related functions within Puploader.
"""
import json
import os
import bcrypt
from flask import (Blueprint, current_app, redirect, render_template,
                   request, session, url_for)
from flask_login import login_user, logout_user
from oauthlib.oauth2 import WebApplicationClient
import pymongo
import requests
from user import User

auth = Blueprint('auth', __name__, template_folder='templates')

GOOGLE_DISCOVERY_URL = (
    "https://accounts.google.com/.well-known/openid-configuration"
)


def get_google_provider_cfg():
    """
    Retrieve Google's Provider resource - For use with Google authentication.
    """
    return requests.get(GOOGLE_DISCOVERY_URL).json()


def db_connect():
    """
    Connect to the MongoDB backend to provide user information.
    """
    if current_app.config['MONGODB_URI']:
        mongo_uri = current_app.config['MONGODB_URI']
    else:
        mongo_uri = '127.0.0.1'

    database = pymongo.MongoClient(mongo_uri, 27017)['AUTH']

    return database['USERS']


# users = db_connect()


@auth.route('/register', methods=['POST', 'GET'])
def register():
    """
    Register Puploader users either via its registration form.
    """
    print(url_for('auth.authenticated'))
    if "username" in session:
        return redirect(url_for('auth.authenticated', _external=True))

    if request.method == 'POST':
        name = request.form.get('inputFirstName')
        username = request.form.get('inputUsername').lower()
        password = request.form.get('inputPassword')
        password_conf = request.form.get('confirmPassword')
        
        users = db_connect()

        if users.find_one({'email': username}):
            return render_template('/auth/register.html',
                                   message='Username already taken.',
                                   auth=('username' in session))

        if password != password_conf:
            return 'Passwords must match.'

        hashed_pw = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
        users.insert_one({'email': username, 'name': name, 'password': hashed_pw})

        return render_template('/auth/authenticated.html',
                               username=name,
                               auth=('username' in session))

    return render_template('/auth/register.html', auth=('username' in session))


@auth.route('/login', methods=['POST', 'GET'])
def login():
    """
    Log users into Puploader via the supplied login form.
    """
    message = None

    if "username" in session:
        return redirect(url_for('auth.authenticated'))

    if request.method == 'POST':
        username = request.form.get('inputUsername')
        password = request.form.get('inputPassword')

        users = db_connect()

        user_record = users.find_one({'email': username.lower()})

        if user_record:
            if bcrypt.checkpw(password.encode('utf-8'),
                              user_record['password']):
                session['username'] = user_record['email']
                return redirect(url_for('auth.authenticated', _external=True))

            message = 'Incorrect password - Please try again.'
            return render_template('/auth/login.html',
                                   message=message,
                                   auth=('username' in session))

        else:
            message = 'Username not found - Please check and try again.'
            return render_template('/auth/login.html',
                                   message=message,
                                   auth=('username' in session))

    return render_template('/auth/login.html',
                           message=message,
                           auth=('username' in session))


@auth.route('/google_auth')
def google_auth():
    """
    Entrypoint for Google-based authentication.
    Sets up google_auth_callback w/ appropriate request URI.
    """
    google_provider_cfg = get_google_provider_cfg()
    auth_endpoint = google_provider_cfg['authorization_endpoint']
    client = WebApplicationClient(current_app.config['GOOGLE_CLIENT_ID'])
    
    request_uri = client.prepare_request_uri(auth_endpoint,
                                             redirect_uri=request.base_url + "/callback",
                                             scope=['openid', 'email', 'profile'],
                                             )

    return redirect(request_uri)


@auth.route('/google_auth/callback')
def google_auth_callback():
    """
    Primary businss logic for Google-related authentication.
    Will create a user in the DB if user is not currently registered.
    """
    auth_code = request.args.get('code')

    google_provider_cfg = get_google_provider_cfg()
    token_endpoint = google_provider_cfg['token_endpoint']
    client = WebApplicationClient(current_app.config['GOOGLE_CLIENT_ID'])

    token_url, headers, body = client.prepare_token_request(
                                                            token_endpoint,
                                                            authorization_response=request.url,
                                                            redirect_url=request.base_url,
                                                            code=auth_code
                                                            )

    token_response = requests.post(token_url, headers=headers, data=body,
                                   auth=(current_app.config['GOOGLE_CLIENT_ID'], current_app.config['GOOGLE_CLIENT_SECRET']),)

    client.parse_request_body_response(json.dumps(token_response.json()))

    userinfo_endpoint = google_provider_cfg['userinfo_endpoint']
    uri, headers, body = client.add_token(userinfo_endpoint)
    userinfo_response = requests.get(uri, headers=headers, data=body)

    if userinfo_response.json().get('email_verified'):
        unique_id = userinfo_response.json()["sub"]
        users_email = userinfo_response.json()["email"]
        # picture = userinfo_response.json()["picture"]
        users_name = userinfo_response.json()["given_name"]
    else:
        print('User not verified.')
        unique_id = userinfo_response.json()["sub"]
        users_email = userinfo_response.json()["email"]
        # picture = userinfo_response.json()["picture"]
        users_name = userinfo_response.json()["given_name"]

    user = User(user_id=unique_id, name=users_name, email=users_email, profile_pic='')

    if not User.get(unique_id):
        User.create(unique_id, users_name, users_email, 'pic_placeholder')

    login_user(user)
    session['username'] = users_email

    return redirect(url_for('auth.authenticated'))


@auth.route('/authenticated')
def authenticated():
    """
    Intermediary landing after users login/register.
    Automatically redirects to index.
    """
    if "username" in session:
        users = db_connect()
        username = session['username']
        name = users.find_one({'email': username})['name']

        return render_template('/auth/authenticated.html',
                               username=name,
                               auth=('username' in session))

    return redirect('/')


@auth.route('/logout', methods=['POST', 'GET'])
def logout():
    """
    Log user out - Remove their information from the session and call logout_user.
    If user is not currently logged in, simply redirect them to the index.
    """
    if 'username' in session:
        logout_user()
        session.pop('username', None)

        return render_template('/auth/logout.html',
                               auth=('username' in session))

    return render_template('/auth/index_unauth.html',
                           auth=('username' in session))
