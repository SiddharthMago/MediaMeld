from flask import Flask, render_template, request, redirect, url_for, flash, session, make_response, jsonify
from flask_jwt_extended import create_access_token, get_jwt_identity, jwt_required, JWTManager
from werkzeug.utils import secure_filename
from datetime import datetime, timedelta

import hashlib
import os
import base64
import json
from pathlib import Path
from dotenv import load_dotenv

from python_db_connector import *
from video_creator import create_video


load_dotenv()

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'heic'}
UPLOAD_PATH = os.getcwd() + '/static/Resources/temp'
USABLE_UPLOAD_PATH = Path(UPLOAD_PATH)

app = Flask(__name__)

app.config["JWT_TOKEN_LOCATION"] = ["headers", "cookies", "json", "query_string"]
app.config['JWT_SECRET_KEY'] = os.getenv('JWT_SECRET_KEY')
app.config['JWT_COOKIE_SECURE'] = False 
app.config["JWT_COOKIE_CSRF_PROTECT"] = False

app.config['IMAGE_UPLOADS'] = UPLOAD_PATH

app.secret_key = os.getenv('JWT_SECRET_KEY')

jwt = JWTManager(app)


def encrypt_string(hash_string):
    sha_signature = hashlib.sha256(hash_string.encode()).hexdigest()
    return sha_signature


def bytes_to_base64(bytes):
    return base64.b64encode(bytes).decode('utf-8')


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def get_list_of_images(user_email, checkbox = False):
    html_text = ""
    image_template = '<div class="li-image"><i class="bx bxs-check-circle select"></i><li><img src="data:image/jpeg;base64,%%IMAGE_DATA%%" loading="lazy"></li></div>'
    if not checkbox:
        image_template = image_template.replace('<i class="bx bxs-check-circle select"></i>', '')

    images = get_images(user_email)
    for image in images:
        image_data = str(bytes(image[0]), 'utf-8')
        html_text += image_template.replace('%%IMAGE_DATA%%', image_data)
    
    return html_text


def get_list_of_audio():
    html_text = ""
    audio_template = '''
    <input type="radio" id="%%AUDIO_ID%%" name="audio" value="%%AUDIO_ID%%">
    <label for="%%AUDIO_ID%%">
        <audio iad="audioid" controls>
        <source src="data:audio/mp3;base64,%%AUDIO_DATA%%" type="audio/mp3"> 
            Your browser does not support the audio element.
    </label><br>
    '''

    for audio in get_audio_ids():
        audio_id = str(audio[0])
        audio_data = str(bytes(audio[1]), 'utf-8')

        curr_html = audio_template
        curr_html = curr_html.replace('%%AUDIO_ID%%', audio_id)
        curr_html = curr_html.replace('%%AUDIO_DATA%%', audio_data)
        html_text += curr_html

    return html_text


@app.route('/')
def init():
    return redirect(url_for('login'))


@app.route('/login', methods=['POST', 'GET'])
def login():
    error = None
    try:
        access_token = request.cookies.get('access_token_cookie')
        if access_token:
            return redirect(url_for('home'))
    except:
        pass

    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')

        user_data = get_from_user_details(email)

        if user_data and encrypt_string(password) == user_data['user_password']:
            # Store user-related information in the session
            session['user_email'] = email
            session['user_name'] = user_data['user_name']
            session['user_id'] = user_data['user_id']

            # Generate JWT token for the user
            access_token = create_access_token(identity=email, expires_delta=timedelta(days=7))
            response = make_response(redirect(url_for('home')))
            response.set_cookie('access_token_cookie', value=access_token, max_age=3600, httponly=True)
            return response

        error = "Invalid username or password. Please try again."
        flash(error, 'error')

    return render_template('login.html')


@app.route('/register', methods=['POST', 'GET'])
def register():
    if request.method == 'POST':
        email = request.form.get('email')
        name = request.form.get('username')
        password = request.form.get('password')
        
        user_data = get_from_user_details(email)
        if user_data:
            flash('User already exists.', 'error')

        else:
            insert_into_user_details(name, email, encrypt_string(password))

        return redirect(url_for('login'))

    return render_template('login.html')
    

@app.route('/home')
@jwt_required()
def home():
    if os.path.exists(f'{os.getcwd()}/static/Resources/temp/{session["user_email"]}.mp4'):
        os.remove(f'{os.getcwd()}/static/Resources/temp/{session["user_email"]}.json')
        os.remove(f'{os.getcwd()}/static/Resources/temp/{session["user_email"]}.mp3')
        os.remove(f'{os.getcwd()}/static/Resources/temp/{session["user_email"]}.mp4')

    return render_template('main_page.html', username = session['user_name'], image_list = get_list_of_images(session['user_email']))


@app.route('/upload', methods=['POST', 'GET'])
@jwt_required()
def upload():
    if request.method == 'POST':
        image = request.files['file']

        if image.filename == '':
            print("File name is invalid")
            return redirect(request.url)


        if image and allowed_file(image.filename):
            filename = secure_filename(image.filename)
            basedir = os.path.abspath(os.path.dirname(__file__))
            image.save(os.path.join(basedir, app.config['IMAGE_UPLOADS'], filename))
            
            for image_path in USABLE_UPLOAD_PATH.iterdir():
                image_bytes = bytes_to_base64(image_path.read_bytes())

                store_image_bytes(image_bytes, session['user_id'], filename, metadata_to_type(filename))
                image_path.unlink()

            return redirect(url_for('upload'))


    current_user = get_jwt_identity()
    return render_template('drag_drop.html')


@app.route('/select_images')
@jwt_required()
def select_images():
    return render_template('select_images.html', image_list = get_list_of_images(session['user_email'], True))


@app.route('/recieve_images', methods=['POST'])
@jwt_required()
def recieve_images():
    if request.method == 'POST':
        with open(f'{os.getcwd()}/static/Resources/temp/{session["user_email"]}.json', 'w') as f:
            f.write(json.dumps(request.json))
        return jsonify({'status': 'success'}), 200

    return jsonify({'status': 'error'}), 404


@app.route('/select_audio', methods=['POST', 'GET'])
@jwt_required()
def select_audio():
    if request.method == 'POST':
        audio_id = request.form.get('audio')
        with open(f'{os.getcwd()}/static/Resources/temp/{session["user_email"]}.json', 'r') as f:
            data = json.load(f)
            data['audio'] = str(bytes(get_audio(audio_id)), 'utf-8')
            with open(f'{os.getcwd()}/static/Resources/temp/{session["user_email"]}.json', 'w') as f:
                f.write(json.dumps(data, indent=4))

        return redirect(url_for('video'))

    return render_template('select_audio.html', audio_list = get_list_of_audio())



@app.route('/video', methods=['POST', 'GET'])
@jwt_required()
def video():
    images = []
    audio = ""
    with open(f'{os.getcwd()}/static/Resources/temp/{session["user_email"]}.json', 'r') as f:
        data = json.load(f)
        images = data['images']
        audio = data['audio']

    clean_images = [image.split('base64,')[1] for image in images]
    
    create_video(clean_images, audio, session["user_email"])

    video_path = f'/Resources/temp/{session['user_email']}.mp4'
    video_src = url_for('static', filename=video_path)
    
    return render_template('video.html', video_src = video_src)


@app.route('/admin')
def admin():
    html_text = ""
    
    user_div_template = '''
    <div class="container-fluid p-5 user-container" style="width: 90vw; height: 50vh;">
        <h3>%%USERNAME%%</h3>
        <span>(%%USER_EMAIL%%)</span>
        <div class="image-container">
            <ul>
                %%IMAGES%%
            </ul>
        </div>
    </div>
    '''

    user_list = get_unique_user_ids()
    for user_id in user_list:
        user_html = user_div_template
        user_html = user_html.replace('%%USERNAME%%', user_id[1])
        user_html = user_html.replace('%%USER_EMAIL%%', user_id[2])
        user_html = user_html.replace('%%IMAGES%%', get_list_of_images(user_id[2]))
        html_text += user_html

    return render_template('admin.html', image_containers = html_text)


if __name__ == '__main__':
    app.run(port="5550", debug=True)
