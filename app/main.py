from app import app
import os
from flask import flash, redirect, render_template, request
from werkzeug.utils import secure_filename
from config import config


@app.route('/')
def puploader_landing():
    return render_template('index.html')


@app.route('/upload')
def puploader_upload():
    folders = [folder for folder in os.listdir(app.config['UPLOAD_FOLDER']) if os.path.isdir(os.path.join(app.config['UPLOAD_FOLDER'], folder))]
    folders.sort()
    return render_template('upload.html', folders=folders)

@app.route('/uploaded', methods=['GET', 'POST'])
def upload_file():
    if request.method == 'POST': # Check for appropriate method
        # Proceed if there are files to upload - Else notify user.
        files = request.files.getlist('files')
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
                file.save(os.path.join(upload_folder, secure_filename(file.filename)))
            
        flash('File(s) uploaded successfully!', 'success')

        return redirect('/upload')
            
    else:
        return 'Something went wrong - Please try again.'


@app.route('/gallery', methods=['GET'])
def render_gallery():
    folders = [folder for folder in os.listdir(app.config['UPLOAD_FOLDER']) if os.path.isdir(os.path.join(app.config['UPLOAD_FOLDER'], folder))]
    folders.sort()
    photos = [photo for photo in os.listdir(config['upload_folder']) if '.' in photo]
    
    return render_template('gallery.html', photos=photos, folders=folders)


@app.route('/gallery/<subfolder>', methods=['GET'])
def render_subfolder_gallery(subfolder):
    subfolder = os.path.join(app.config['UPLOAD_FOLDER'], subfolder)
    folders = [folder for folder in os.listdir(app.config['UPLOAD_FOLDER']) if os.path.isdir(os.path.join(subfolder, folder))]
    folders.sort()
    photos = [photo for photo in os.listdir(subfolder) if '.' in photo]

    return render_template('gallery.html', photos=photos, folders=folders)

if __name__ == '__main__':
    app.run()
