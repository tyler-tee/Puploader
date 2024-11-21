"""
This is the primary entrypoint for Puploader.
"""
import os
from flask import render_template, session, url_for
from flask_login import LoginManager
from views.photos import get_s3_photos
from app import create_app


app, users = create_app()
login_manager = LoginManager()
login_manager.init_app(app)


@login_manager.user_loader
def load_user(user_id):
    """
    Retrieve user information based on their unique ID.
    """
    return users.find_one({'user_id': user_id})['user_id']


@app.route('/')
def puploader_landing():
    """
    Puploader's landing page.
    Renders index.html/index_unauth.html based on session information.
    """
    if app.config['S3_BUCKET']:
        bucket_name = "https://puploader.s3.us-east-2.amazonaws.com/"
        photos = get_s3_photos()
        photos = [f'{bucket_name}' + photo for photo in photos]
    else:
        photos = [photo for photo in os.listdir(app.config['UPLOAD_FOLDER']) if '.' in photo]
        photos = [url_for('static', filename='uploads/' + photo) for photo in photos]

    if "username" in session:
        return render_template('index.html', photos=photos, auth=("username" in session))

    return render_template('index_unauth.html', photos=photos, auth=False)


@app.route('/about', methods=['GET'])
def render_about():
    """
    Route responsible for rendering Puploader's About page.
    """
    return render_template('about.html', auth=('username' in session))


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
