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

AUTH_LOGIN = 'auth.login'


def list_folders(base_path: str) -> List[str]:
    """List all subfolders in the given base path."""
    return sorted([folder for folder in os.listdir(base_path) if os.path.isdir(os.path.join(base_path, folder))])


def get_s3_photos(bucket_name: str = 'puploader') -> List[str]:
    """Retrieve all photo keys from an S3 bucket."""
    s3_client = boto3.client('s3')
    response = s3_client.list_objects_v2(Bucket=bucket_name)
    return [obj['Key'] for obj in response.get('Contents', [])]


def resolve_duplicate_filename(filename: str, existing_files: List[str]) -> str:
    """Resolve duplicate filenames by appending '_dupe'."""
    while filename in existing_files:
        name, extension = os.path.splitext(filename)
        filename = f"{name}_dupe{extension}"
    return filename


def cleanup_directory(directory: str, max_files: int):
    """Remove oldest files if the directory exceeds the allowed limit."""
    files = [(f, os.path.getmtime(os.path.join(directory, f))) for f in os.listdir(directory)]
    files.sort(key=lambda x: x[1])  # Sort by modification time
    while len(files) > max_files:
        os.remove(os.path.join(directory, files.pop(0)[0]))


def upload_to_s3(file, bucket_name: str):
    """Upload a file to S3."""
    bucket = boto3.resource('s3').Bucket(bucket_name)
    bucket.Object(file.filename).put(Body=file)


@photos.route('/upload')
def puploader_upload():
    """Entry route for Puploader's photo upload functionality."""
    if "username" in session:
        folders = list_folders(current_app.config['UPLOAD_FOLDER'])
        return render_template('/photos/upload.html', folders=folders, auth=('username' in session))
    return redirect(url_for(AUTH_LOGIN))


@photos.route('/uploaded', methods=['POST'])
def upload_file():
    """Handle photo uploads for private or public instances."""
    if "username" not in session:
        return redirect(url_for(AUTH_LOGIN))

    files = request.files.getlist('files')
    if not files or not files[0].filename:
        flash('No file to upload - Please try again.', 'error')
        return redirect('/upload')

    folder_name = request.form.get('folder_dropdown', 'default').lower()
    upload_folder = (os.path.join(current_app.config['UPLOAD_FOLDER'], secure_filename(folder_name))
                     if folder_name != 'default' else current_app.config['UPLOAD_FOLDER'])

    existing_files = (os.listdir(upload_folder) if current_app.config['PRIVATE'] else get_s3_photos())
    for file in files:
        if not file.filename.split('.')[-1].lower() in {'gif', 'jpg', 'jpeg', 'png'}:
            continue

        file.filename = resolve_duplicate_filename(file.filename, existing_files)

        if current_app.config['PRIVATE']:
            if len(os.listdir(upload_folder)) >= current_app.config['UPLOAD_FOLDER_MAX']:
                cleanup_directory(upload_folder, current_app.config['UPLOAD_FOLDER_MAX'])
            file.save(os.path.join(upload_folder, secure_filename(file.filename)))
        else:
            upload_to_s3(file, 'puploader')

    flash('File(s) uploaded successfully!', 'success')
    return redirect('/upload')


@photos.route('/sign_s3/')
def sign_s3():
    """Generate a presigned URL for S3 photo uploads."""
    s3_bucket = os.environ.get('S3_BUCKET', current_app.config['S3_BUCKET'])
    file_name = secure_filename(request.args.get('file_name', ''))
    file_type = request.args.get('file_type', '')
    s3_client = boto3.client('s3')
    presigned_post = s3_client.generate_presigned_post(
        Bucket=s3_bucket,
        Key=file_name,
        Fields={"acl": "public-read", "Content-Type": file_type},
        Conditions=[{"acl": "public-read"}, {"Content-Type": file_type}],
        ExpiresIn=3600
    )
    return json.dumps({'data': presigned_post, 'url': f'https://{s3_bucket}.s3.amazonaws.com/{file_name}'})


@photos.route('/new_folder', methods=['POST'])
def create_new_folder():
    """Allow private instances to create new folders for uploads."""
    if not current_app.config['PRIVATE']:
        flash("Sorry, new folder creation is disabled while running publicly!")
        return redirect('upload')

    new_folder = secure_filename(request.form.get('folderName', '')).lower()
    new_folder_path = os.path.join(current_app.config['UPLOAD_FOLDER'], new_folder)

    try:
        os.mkdir(new_folder_path)
        flash(f'New folder "{new_folder}" created!')
    except FileExistsError:
        flash('Folder already exists - No folder created.')
    return redirect('upload')


@photos.route('/gallery', methods=['GET'])
def render_gallery():
    """Render Puploader's photo gallery."""
    if "username" not in session:
        return redirect(url_for(AUTH_LOGIN))

    if current_app.config['S3_BUCKET']:
        bucket_url = f"https://{current_app.config['S3_BUCKET']}.s3.amazonaws.com/"
        photos = [f"{bucket_url}{photo}" for photo in get_s3_photos()]
        folders = []
    else:
        folders = list_folders(current_app.config['UPLOAD_FOLDER'])
        photos = [photo for photo in os.listdir(current_app.config['UPLOAD_FOLDER']) if '.' in photo]

    return render_template('/photos/gallery.html', photos=photos, folders=folders, auth=True)


@photos.route('/gallery/<subfolder>', methods=['GET'])
def render_subfolder_gallery(subfolder):
    """Render photos from a specific subfolder."""
    if '.' in subfolder or "username" not in session:
        return redirect(url_for(AUTH_LOGIN))

    safe_subfolder = secure_filename(subfolder)
    subfolder_dir = os.path.join(current_app.config['UPLOAD_FOLDER'], safe_subfolder)
    folders = list_folders(subfolder_dir)
    photos = [f"{safe_subfolder}/{photo}" for photo in os.listdir(subfolder_dir) if '.' in photo]

    return render_template('/photos/gallery.html', photos=photos, folders=folders, auth=True)
