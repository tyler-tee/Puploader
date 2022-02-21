from app import app
import os
from flask import flash, redirect, render_template, request
from werkzeug.utils import secure_filename


@app.route('/')
def puploader_landing():
    return render_template('upload.html')

@app.route('/upload', methods=['GET', 'POST'])
def upload_file():
    print(request.method)
    if request.method == 'POST': # Check for appropriate method
        # Proceed if there are files to upload - Else notify user.
        files = request.files.getlist('files')
        
        for file in files:
            extension = file.filename.split('.')[-1].lower()
            
            if extension in ('gif', 'jpg', 'jpeg', 'png'):
                file.save(os.path.join(app.config['UPLOAD_FOLDER'],
                                        secure_filename(file.filename)))
            
        flash('File(s) uploaded successfully!', 'success')
        
        return redirect('/')
            
    else:
        return 'Something went wrong - Please try again.'

if __name__ == '__main__':
    app.run()
