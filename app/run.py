"""
This is the primary entrypoint for Puploader.
"""
import os
from flask import redirect, render_template, request, session, url_for
from flask_login import LoginManager
from views.photos import get_s3_photos
from app import create_app


app, users, petfinder_api = create_app()
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


@app.route('/resources/<resource>', methods=['GET', 'POST'])
def render_resources(resource):
    """
    Route responsible for rendering pages related to animal-friendly resources.
    """
    petfinder_api.auth()

    location = request.form.get('inputZip')

    if resource == 'local_pups':
        pups = petfinder_api.get_animals(type='dog', location=location)

        for pup in pups:
            pup['contact']['address'] = ', '.join(i for i in pup['contact']['address'].values()
                                                  if i)
            try:
                pup['photo'] = pup['photos'][0]['medium']
            except IndexError:
                pup['photo'] = url_for('static', filename='/assets/no_photo_avail.jpg')

        return render_template('/resources/pups.html', pups=pups, auth=('username' in session))

    elif resource == 'local_orgs':
        organizations = petfinder_api.get_organizations(location=location)

        for org in organizations:
            org['address'] = ', '.join(i for i in org['address'].values() if i)
            org['hours'] = ', '.join(i for i in org['hours'].values() if i)
            try:
                org['photo'] = org['photos'][0]['medium']
            except IndexError:
                org['photo'] = ''

        return render_template('/resources/organizations.html',
                               organizations=organizations,
                               auth=('username' in session))

    elif resource == 'charities':
        return render_template('/resources/charities.html')

    return redirect('/')


@app.route('/about', methods=['GET'])
def render_about():
    """
    Route responsible for rendering Puploader's About page.
    """
    return render_template('about.html', auth=('username' in session))


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, ssl_context="adhoc")
