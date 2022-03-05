from distutils.log import Log
from enum import unique
import bcrypt
import boto3
from flask import flash, redirect, render_template, request, session, url_for
from flask_login import LoginManager, current_user, login_required, login_user, logout_user
import json
from oauthlib.oauth2 import WebApplicationClient
import os
import requests
from werkzeug.utils import secure_filename
from app import create_app
from user import User


app, users, petfinder_api = create_app()


GOOGLE_CLIENT_ID = os.environ.get("GOOGLE_CLIENT_ID", None)
GOOGLE_CLIENT_SECRET = os.environ.get("GOOGLE_CLIENT_SECRET", None)
GOOGLE_DISCOVERY_URL = (
    "https://accounts.google.com/.well-known/openid-configuration"
)

login_manager = LoginManager()
login_manager.init_app(app)
client = WebApplicationClient(GOOGLE_CLIENT_ID)


def get_google_provider_cfg():
    return requests.get(GOOGLE_DISCOVERY_URL).json()


@login_manager.user_loader
def load_user(user_id):
    return users.find_one({'user_id': user_id})['user_id']


def get_s3_photos():
    s3 = boto3.client('s3')
    objects = s3.list_objects_v2(Bucket='puploader')['Contents']
    objects = [obj['Key'] for obj in objects]
    
    return objects


@app.route('/')
def puploader_landing():
    if app.config['S3_BUCKET']:
        bucket_name = "https://puploader.s3.us-east-2.amazonaws.com/"
        photos = get_s3_photos()
        photos = [f'{bucket_name}' + photo for photo in photos]
    else:
        photos = [photo for photo in os.listdir(app.config['UPLOAD_FOLDER']) if '.' in photo]
        photos = [url_for('static', filename='uploads/' + photo) for photo in photos]

    if "username" in session:
        return render_template('index.html', photos=photos, auth=("username" in session))
    
    else:
        return render_template('index_unauth.html', photos=photos, auth=False)


@app.route('/register', methods=['POST', 'GET'])
def register():
    if User.is_authenticated:
        return redirect(url_for('authenticated'))
    
    if "username" in session:
        return redirect(url_for('authenticated'))
    
    if request.method == 'POST':
        username = request.form.get('inputUsername').lower()
        password = request.form.get('inputPassword')
        password_conf = request.form.get('confirmPassword')
        
        if users.find_one({'username': username}):
            return render_template('register.html', message='Username already taken.', auth=('username' in session))
        
        if password != password_conf:
            return 'Passwords must match.'
        
        else:
            hashed_pw = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
            users.insert_one({'username': username, 'password': hashed_pw})
            
            return render_template('authenticated.html', username=username.title(), auth=('username' in session))
        
    return render_template('register.html', auth=('username' in session))


@app.route('/login', methods=['POST', 'GET'])
def login():
    message = None
    
    if "username" in session:
        return redirect(url_for('authenticated'))

    if request.method == 'POST':
        username = request.form.get('inputUsername')
        password = request.form.get('inputPassword')
        
        user_record = users.find_one({'username': username.lower()})
        
        if user_record: 
            if bcrypt.checkpw(password.encode('utf-8'), user_record['password']):
                session['username'] = user_record['username']
                return redirect(url_for('authenticated'))
            else:
                message = 'Incorrect password - Please try again.'
                return render_template('login.html', message=message, auth=('username' in session))
        
        else:
            message = 'Username not found - Please check and try again.'
            return render_template('login.html', message=message, auth=('username' in session))
            
    else:
        return render_template('login.html', message=message, auth=('username' in session))


@app.route('/google_auth')
def google_auth():
    google_provider_cfg = get_google_provider_cfg()
    auth_endpoint = google_provider_cfg['authorization_endpoint']
    
    request_uri = client.prepare_request_uri(auth_endpoint,
                                             redirect_uri=request.base_url + "/callback",
                                             scope=['openid', 'email', 'profile'],
                                             )
    
    return redirect(request_uri)


@app.route('/google_auth/callback')
def google_auth_callback():
    auth_code = request.args.get('code')
    
    google_provider_cfg = get_google_provider_cfg()
    token_endpoint = google_provider_cfg['token_endpoint']
    
    token_url, headers, body = client.prepare_token_request(
                                                            token_endpoint,
                                                            authorization_response=request.url,
                                                            redirect_url=request.base_url,
                                                            code=auth_code
                                                            )
    
    token_response = requests.post(token_url, headers=headers, data=body,
                                   auth=(GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET),)
    
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
        
    return redirect(url_for('authenticated'))


@app.route('/authenticated')
def authenticated():
    if  "username" in session:
        username = session['username']
        name = users.find_one({'email': username})['name']
        
        return render_template('authenticated.html', username=name, auth=('username' in session))


@app.route('/upload')
def puploader_upload():
    if "username" in session:
        folders = [folder for folder in os.listdir(app.config['UPLOAD_FOLDER']) if os.path.isdir(os.path.join(app.config['UPLOAD_FOLDER'], folder))]
        folders.sort()
        return render_template('upload.html', folders=folders, auth=('username' in session))
    
    else:
        return redirect(url_for('login'))
    
    
def dir_cleanup():
    files = {i: os.path.getmtime(i) for i in os.listdir(app.config['UPLOAD_FOLDER'])}
    
    os.remove(files[0][0])
    

@app.route('/uploaded', methods=['GET', 'POST'])
def upload_file():
    if "username" in session:
        if request.method == 'POST': # Check for appropriate method
            # Proceed if there are files to upload - Else notify user.
            files = request.files.getlist('files')
            
            if not files[0].filename:
                flash('No file to upload - Please try again.', 'error')
                return redirect('/upload')
            
            if request.form['folder_dropdown'].lower() != 'default':
                upload_folder = os.path.join(app.config['UPLOAD_FOLDER'], request.form['folder_dropdown'])
            else:
                upload_folder = app.config['UPLOAD_FOLDER']
            
            if app.config['PRIVATE']:
                for file in files:
                    extension = file.filename.split('.')[-1].lower()
                    
                    if extension in ('gif', 'jpg', 'jpeg', 'png'): # Check for allowed extensions
                        # If filename is a duplicate, tag w/ _dupe
                        while file.filename in os.listdir(upload_folder):
                            file.filename = '.'.join(file.filename.split('.')[:-1]) + '_dupe.' + extension
                        
                        if len(os.listdir('.')) >= app.config['UPLOAD_FOLDER_MAX']:
                            dir_cleanup()
                        
                        file.save(os.path.join(upload_folder, secure_filename(file.filename)))
            else:
                for file in files:
                    extension = file.filename.split('.')[-1].lower()
                    
                    if extension in ('gif', 'jpg', 'jpeg', 'png'): # Check for allowed extensions
                        # If filename is a duplicate, tag w/ _dupe
                        while file.filename in get_s3_photos():
                            file.filename = '.'.join(file.filename.split('.')[:-1]) + '_dupe.' + extension                
                        
                        # Upload photo to s3 bucket
                        bucket = boto3.resource('s3').Bucket('puploader')
                        bucket.Object(file.filename).put(Body=file)
                
            flash('File(s) uploaded successfully!', 'success')

            return redirect('/upload')
                
        else:
            return 'Something went wrong - Please try again.'
    else:
        return redirect(url_for('login'))
    
    
@app.route('/sign_s3/')
def sign_s3():
  S3_BUCKET = os.environ.get('S3_BUCKET') if os.environ.get('S3_BUCKET') else app.config['S3_BUCKET']
  file_name = request.args.get('file_name')
  file_type = request.args.get('file_type')
  s3 = boto3.client('s3')
  presigned_post = s3.generate_presigned_post(Bucket=S3_BUCKET, Key=file_name,
                                              Fields = {"acl": "public-read", "Content-Type": file_type},
                                              Conditions = [
                                                            {"acl": "public-read"},
                                                            {"Content-Type": file_type}
                                                            ],
                                              ExpiresIn = 3600
                                              )
  
  return json.dumps({'data': presigned_post,
                    'url': f'https://{S3_BUCKET}.s3.amazonaws.com/{file_name}' % (S3_BUCKET, file_name)})

    
@app.route('/new_folder', methods=['POST', 'GET'])
def create_new_folder():
    if app.config['PRIVATE']:
        new_folder = request.form['folderName'].replace('.', '').replace('/', '').replace('\\', '')
        
        try:
            os.mkdir(os.path.join(app.config['UPLOAD_FOLDER'], new_folder))
            
            flash('New folder ' + new_folder + ' created!')
            
            return redirect('upload')
        
        except Exception as e:
            print(e)
            
            flash('Folder already exists - No folder created.')
            return redirect('upload')
    else:
        flash("Sorry, new folder creation is disabled while running publicly!")
        return redirect('upload')


@app.route('/gallery', methods=['GET'])
def render_gallery():
    if "username" in session:
        folders = [folder for folder in os.listdir(app.config['UPLOAD_FOLDER']) if os.path.isdir(os.path.join(app.config['UPLOAD_FOLDER'], folder))]
        folders.sort()
        photos = [photo for photo in os.listdir(app.config['UPLOAD_FOLDER']) if '.' in photo]
        
        return render_template('gallery.html', photos=photos, folders=folders, auth=('username' in session))
    else:
        return redirect(url_for('login'))


@app.route('/gallery/<subfolder>', methods=['GET'])
def render_subfolder_gallery(subfolder):
    if '.' in subfolder:
        return redirect(url_for('/'))
    
    if "username" in session:
        subfolder_dir = os.path.join(app.config['UPLOAD_FOLDER'], subfolder)
        folders = [folder for folder in os.listdir(app.config['UPLOAD_FOLDER']) if os.path.isdir(os.path.join(subfolder_dir, folder))]
        folders.sort()
        photos = [subfolder + '/' + photo for photo in os.listdir(subfolder_dir) if '.' in photo]

        return render_template('gallery.html', photos=photos, folders=folders, auth=('username' in session))
    else:
        return redirect(url_for('login'))
    
    
@app.route('/resources/<resource>', methods=['GET', 'POST'])
def render_resources(resource):
    petfinder_api.auth()
    
    try:
        location = int(request.form.get('inputZip'))
    except Exception as e:
        print(e)
        location = None
    
    if resource == 'local_pups':
        pups = petfinder_api.get_animals(type='dog', location=location)
    
        for pup in pups:
            pup['contact']['address'] = ', '.join(i for i in pup['contact']['address'].values() if i)
            try:
                pup['photo'] = pup['photos'][0]['medium']
            except Exception as e:
                pup['photo'] = url_for('static', filename='/assets/no_photo_avail.jpg')

        return render_template('pups.html', pups=pups, auth=('username' in session))
    
    elif resource == 'local_orgs':
        organizations = petfinder_api.get_organizations(location=location)
    
        for org in organizations:
            org['address'] = ', '.join(i for i in org['address'].values() if i)
            org['hours'] = ', '.join(i for i in org['hours'].values() if i)
            try:
                org['photo'] = org['photos'][0]['medium']
            except Exception as e:
                org['photo'] = ''
    
        return render_template('organizations.html', organizations=organizations, auth=('username' in session))
    
    elif resource == 'charities':
        return "Coming soon!"


@app.route('/about', methods=['GET'])
def render_about():
    return render_template('about.html', auth=('username' in session))


@app.route('/logout', methods=['POST', 'GET'])
def logout():
    if 'username' in session:
        session.pop('username', None)
        
        return render_template('logout.html', auth=('username' in session))
    
    else:
        return render_template('index_unauth.html', auth=('username' in session))


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, ssl_context="adhoc")