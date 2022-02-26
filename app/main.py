from app import app, users
import bcrypt
import os
from flask import flash, redirect, render_template, request, session, url_for
from werkzeug.utils import secure_filename
from config import config
from petfinder_api.petfinder_api import PetFinder


@app.route('/')
def puploader_landing():
    photos = [photo for photo in os.listdir(config['upload_folder']) if '.' in photo]

    if "username" in session:
        return render_template('index.html', photos=photos)
    else:
        return render_template('index_unauth.html', photos=photos)


@app.route('/register', methods=['POST', 'GET'])
def register():
    if "username" in session:
        return redirect(url_for('authenticated'))
    
    if request.method == 'POST':
        username = request.form.get('inputUsername').lower()
        password = request.form.get('inputPassword')
        password_conf = request.form.get('confirmPassword')
        
        if users.find_one({'username': username}):
            return render_template('register.html', message='Username already taken.')
        
        if password != password_conf:
            return 'Passwords must match.'
        
        else:
            hashed_pw = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
            users.insert_one({'username': username, 'password': hashed_pw})
            
            return render_template('authenticated.html', username=username.title())
        
    return render_template('register.html')


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
                return render_template('login.html', message=message)
        
        else:
            message = 'Username not found - Please check and try again.'
            return render_template('login.html', message=message)
            
    else:
        return render_template('login.html', message=message)


@app.route('/authenticated')
def authenticated():
    if "username" in session:
        username = session['username']
        
        return render_template('authenticated.html', username=username.title())


@app.route('/upload')
def puploader_upload():
    if "username" in session:
        folders = [folder for folder in os.listdir(app.config['UPLOAD_FOLDER']) if os.path.isdir(os.path.join(app.config['UPLOAD_FOLDER'], folder))]
        folders.sort()
        return render_template('upload.html', folders=folders)
    
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
            
            for file in files:
                extension = file.filename.split('.')[-1].lower()
                
                if extension in ('gif', 'jpg', 'jpeg', 'png'): # Check for allowed extensions
                    # If filename is a duplicate, tag w/ _dupe
                    while file.filename in os.listdir(upload_folder):
                        file.filename = '.'.join(file.filename.split('.')[:-1]) + '_dupe.' + extension
                    
                    if len(os.listdir('.')) >= app.config['upload_folder_max']:
                        dir_cleanup()
                        
                    file.save(os.path.join(upload_folder, secure_filename(file.filename)))
                
            flash('File(s) uploaded successfully!', 'success')

            return redirect('/upload')
                
        else:
            return 'Something went wrong - Please try again.'
    else:
        return redirect(url_for('login'))
    
    
@app.route('/new_folder', methods=['POST', 'GET'])
def create_new_folder():
    if app.config['private']:
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
        photos = [photo for photo in os.listdir(config['upload_folder']) if '.' in photo]
        
        return render_template('gallery.html', photos=photos, folders=folders)
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

        return render_template('gallery.html', photos=photos, folders=folders)
    else:
        return redirect(url_for('login'))
    
    
@app.route('/resources', methods=['GET'])
def render_resources():
    return render_template('resources.html')


@app.route('/about', methods=['GET'])
def render_about():
    return render_template('about.html')


@app.route('/logout', methods=['POST', 'GET'])
def logout():
    if 'username' in session:
        session.pop('username', None)
        
        return render_template('logout.html')
    
    else:
        return render_template('index_unauth.html')


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
