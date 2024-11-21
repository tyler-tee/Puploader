"""
This view contains all routes needed to upload, retrieve, and view photos.
"""
import json
import os
from typing import List
import boto3
from flask import (Blueprint, current_app, escape, flash,
                   redirect, render_template, request,
                   session, url_for)
from werkzeug.utils import secure_filename


photos = Blueprint('photos', __name__, template_folder='templates')


def get_s3_photos() -> List:
    """
    Retrieve all photos from Puploader's S3 bucket.
    """
    s3_client = boto3.client('s3')
    objects = s3_client.list_objects_v2(Bucket='puploader')['Contents']
    objects = [obj['Key'] for obj in objects]

    return objects


@photos.route('/upload')
def puploader_upload():
    """
    Entry route for Puploader's photo upload functionality.
    """
    if "username" in session:
        folders = [folder for folder in os.listdir(current_app.config['UPLOAD_FOLDER'])
                   if os.path.isdir(os.path.join(current_app.config['UPLOAD_FOLDER'], folder))]
        folders.sort()
        return render_template('/photos/upload.html', folders=folders, auth=('username' in session))

    return redirect(url_for('auth.login'))


def dir_cleanup():
    """
    Primarily used for a privately-hosted version of Puploader.
    Removes oldest photo from upload folder.
    """
    files = {i: os.path.getmtime(i) for i in os.listdir(current_app.config['UPLOAD_FOLDER'])}

    os.remove(files[0][0])


@photos.route('/uploaded', methods=['GET', 'POST'])
def upload_file():
    """
    Business logic for Puploader's photo uploads.
    Expected scenario would be a private instance uploading to a folder on the same server,
    whereas a publicly-available instance would upload to an S3 bucket instead.
    """
    if "username" in session:
        if request.method == 'POST':  # Check for appropriate method
            # Proceed if there are files to upload - Else notify user.
            files = request.files.getlist('files')

            if not files[0].filename:
                flash('No file to upload - Please try again.', 'error')
                return redirect('/upload')

            folder_name = request.form['folder_dropdown'].lower()

            if request.form['folder_dropdown'].lower() != 'default':
                upload_folder = os.path.join(current_app.config['UPLOAD_FOLDER'],
                                             secure_filename(folder_name))
            else:
                upload_folder = current_app.config['UPLOAD_FOLDER']

            if current_app.config['PRIVATE']:
                for file in files:
                    extension = file.filename.split('.')[-1].lower()

                    if extension in ('gif', 'jpg', 'jpeg', 'png'):  # Check for allowed extensions
                        # If filename is a duplicate, tag w/ _dupe
                        while file.filename in os.listdir(upload_folder):
                            file.filename = '.'.join(file.filename.split('.')[:-1])
                            file.filename += '_dupe.' + extension

                        if len(os.listdir('.')) >= current_app.config['UPLOAD_FOLDER_MAX']:
                            dir_cleanup()

                        file.save(os.path.join(upload_folder, secure_filename(file.filename)))
            else:
                for file in files:
                    extension = file.filename.split('.')[-1].lower()

                    if extension in ('gif', 'jpg', 'jpeg', 'png'):  # Check for allowed extensions
                        # If filename is a duplicate, tag w/ _dupe
                        while file.filename in get_s3_photos():
                            file.filename = '.'.join(file.filename.split('.')[:-1])
                            file.filename += '_dupe.' + extension

                        # Upload photo to s3 bucket
                        bucket = boto3.resource('s3').Bucket('puploader')
                        bucket.Object(file.filename).put(Body=file)

            flash('File(s) uploaded successfully!', 'success')

            return redirect('/upload')

        return 'Something went wrong - Please try again.'

    return redirect(url_for('auth.login'))


@photos.route('/sign_s3/')
def sign_s3():
    """
    Used to provide Puploader's S3 bucket with a signature for photo uploads.
    """
    if os.environ.get('S3_BUCKET'):
        s3_bucket = os.environ.get('S3_BUCKET')
    else:
        s3_bucket = current_app.config['S3_BUCKET']

    raw_file_name = request.args.get('file_name')
    file_name = secure_filename(raw_file_name)
    file_type = request.args.get('file_type')
    s3_client = boto3.client('s3')
    presigned_post = s3_client.generate_presigned_post(Bucket=s3_bucket, Key=file_name,
                                                       Fields={"acl": "public-read",
                                                               "Content-Type": file_type},
                                                       Conditions=[
                                                                    {"acl": "public-read"},
                                                                    {"Content-Type": file_type}
                                                                    ],
                                                       ExpiresIn=3600
                                                       )

    return json.dumps({'data': presigned_post,
                       'url': f'https://{s3_bucket}.s3.amazonaws.com/{file_name}'})


@photos.route('/new_folder', methods=['POST', 'GET'])
def create_new_folder():
    """
    Allows users to create a new upload folder, should they wish to do so.
    Primarily expected to be leveraged by a private instance.
    """
    if current_app.config['PRIVATE']:
        raw_new_folder = escape(request.form['folderName']).lower()
        new_folder = raw_new_folder.replace('.', '').replace('/', '').replace('\\', '')

        try:
            os.mkdir(os.path.join(current_app.config['UPLOAD_FOLDER'], new_folder))

            flash('New folder ' + new_folder + ' created!')

            return redirect('upload')

        except FileExistsError:

            flash('Folder already exists - No folder created.')
            return redirect('upload')
    else:
        flash("Sorry, new folder creation is disabled while running publicly!")
        return redirect('upload')


@photos.route('/gallery', methods=['GET'])
def render_gallery():
    """
    Route responsible for rendering Puploader's gallery.
    Intended to be used to display uploaded user photos (of dogs).
    """
    if "username" in session:
        if current_app.config['S3_BUCKET']:
            bucket_name = "https://puploader.s3.us-east-2.amazonaws.com/"
            photos = get_s3_photos()
            photo_lst = [f'{bucket_name}' + photo for photo in photos]
            folders = []
        else:
            folders = [folder for folder in os.listdir(current_app.config['UPLOAD_FOLDER'])
                       if os.path.isdir(os.path.join(current_app.config['UPLOAD_FOLDER'], folder))]
            folders.sort()
            photo_lst = [photo for photo in os.listdir(current_app.config['UPLOAD_FOLDER'])
                         if '.' in photo]

        return render_template('/photos/gallery.html',
                               photos=photo_lst,
                               folders=folders,
                               auth=('username' in session))

    return redirect(url_for('auth.login'))


@photos.route('/gallery/<subfolder>', methods=['GET'])
def render_subfolder_gallery(subfolder):
    """
    Render photos within subfolders present in the primary upload folder.
    """
    if '.' in subfolder:
        return redirect(url_for('/'))

    if "username" in session:
        safe_subfolder = escape(subfolder)
        subfolder_dir = os.path.join(current_app.config['UPLOAD_FOLDER'], safe_subfolder)
        folders = [folder for folder in os.listdir(current_app.config['UPLOAD_FOLDER'])
                   if os.path.isdir(os.path.join(subfolder_dir, folder))]
        folders.sort()
        photo_lst = [subfolder + '/' + photo for photo in os.listdir(subfolder_dir)
                     if '.' in photo]

        return render_template('/photos/gallery.html',
                               photos=photo_lst,
                               folders=folders,
                               auth=('username' in session))

    return redirect(url_for('auth.login'))
