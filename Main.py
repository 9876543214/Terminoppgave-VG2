#! C:\Program Files\Python312\python.exe

import os
from flask import Flask, request, redirect, url_for, render_template, send_from_directory, jsonify, session
import pymysql
from werkzeug.utils import secure_filename
from datetime import datetime
import bcrypt


app = Flask(__name__)

app.secret_key = 'your secret key'

displayerr = False
preverr_home = None
preverr_login = None

db_config = {
    'host': '10.2.3.235',
    'user': 'sosial',
    'password': 'sosial123',
    'db': 'sosial_media'
}


# upload mappe
UPLOAD_FOLDER = r'\\10.2.3.235\sambashare'
ALLOWED_EXTENSIONS = {'jpeg', 'mpeg', 'mp4', 'avi', 'mov', 'gif', 'png', 'tiff', 'bmp', 'pdf', 'svg', 'webp', 'avif', 'avi'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Sjekker om fil er gyldig filtype
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/')
def home():
    global displayerr
    global preverr_home
    err = request.args.get('err', 0)
    
    if displayerr == False:
        if preverr_home == err:
            preverr_home = None
            return redirect(url_for('home'))
            
    preverr_home = err
    displayerr = False

    conn = pymysql.connect(**db_config)
    cursor = conn.cursor(pymysql.cursors.DictCursor)

    # Velger tilfeldig posts
    try:
        sql = """
            SELECT post_id, user_id, content, media_path, created_at, visibility, like_count, comment_count
            FROM posts
            WHERE is_deleted = FALSE
            ORDER BY RAND() LIMIT 20
        """
        cursor.execute(sql)
        posts = cursor.fetchall() 
    except Exception as e:
        print(f"Error: {e}")
        posts = []
    finally:
        cursor.close()
        conn.close()

    try:
        files = os.listdir(UPLOAD_FOLDER)
    except Exception as e:
        print(f"Error reading shared folder: {e}")
        files = []

    return render_template('index.html', posts=posts, files=files, err=err)


@app.route('/media/<filename>')
def serve_file(filename):
    try:
        return send_from_directory(UPLOAD_FOLDER, filename)
    except Exception as e:
        print(f"Error serving file {filename}: {e}")
        return "File not found", 404


@app.route('/submit-post', methods=['POST'])
def submit_post():
    global displayerr
    # database
    conn = pymysql.connect(**db_config)
    cursor = conn.cursor()
    if session['user_id'] == None:
        displayerr = True
        return redirect(url_for('home', err=2))
    else:
        user_id = session['user_id']


    # Henter html form
    content = request.form.get('content')
    visibility = request.form.get('visibility')

    # tid og dato
    created_at = datetime.now()

    # Sende media
    media_path = None
    if 'media' in request.files:
        media_file = request.files['media']
        if media_file and allowed_file(media_file.filename):
            # Secure the filename and save the file to the UPLOAD_FOLDER
            filename = secure_filename(media_file.filename)
            
            media_file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            media_path = filename  # Save path for database
        else:
            print("invalid file type")
            displayerr = True
            return redirect(url_for('home', err=1))
            

    # sett inn i databasen
    try:
        sql = """
            INSERT INTO posts (user_id, content, media_path, visibility, created_at)
            VALUES (%s, %s, %s, %s, %s)
        """
        cursor.execute(sql, (user_id, content, media_path, visibility, created_at)) 
        conn.commit()
    except Exception as e:
        print(f"Error: {e}")
        conn.rollback()
    finally:
        cursor.close()
        conn.close()

    # Redirect to the homepage or another page after submission
    return redirect(url_for('home', err=0))


@app.route('/register')
def registerpage():
    return render_template('register.html')

@app.route('/process-register', methods=['POST'])
def process_register():
    conn = pymysql.connect(**db_config)
    cursor = conn.cursor()
    username = request.form.get('username')
    email = request.form.get('email')
    password = request.form.get('password')
    joindate = datetime.now()
    password_bytes = password.encode('utf-8')


    salt = bcrypt.gensalt()

    hashed_password = bcrypt.hashpw(password_bytes, salt)
    

    try:
        sql = """
            INSERT INTO users (username, email, password_hash, join_date, salt)
            VALUES (%s, %s, %s, %s, %s)
            """
        cursor.execute(sql, (username, email, hashed_password, joindate, salt))
        conn.commit()
    except Exception as e:
        print(f"Error: {e}")
        conn.rollback()
        return redirect(url_for('registerpage', err = {e}))
    finally:
        cursor.close()
        conn.close()
    return redirect(url_for('register_success'))
    

@app.route('/register_success')
def register_success():
    return render_template('register_success.html')




@app.route('/validate_email')
def validate_email():
    email = request.args.get('email')
    conn = pymysql.connect(**db_config)
    cursor = conn.cursor()

    sql = """
    SELECT email FROM users WHERE email = %s
    """
    cursor.execute(sql, (email,))
    result = cursor.fetchone()

    conn.close()

    if result:
        return jsonify({"exists": True, "email": result[0]})
    else:
        return jsonify({"exists": False})


@app.route('/login')
def login_page():
    global displayerr
    err = request.args.get('err', 0)
    
    if displayerr == True:
        return redirect(url_for('login_page'))
    
    displayerr = False

    return render_template('login.html', err=err)

@app.route('/login_process', methods=['POST'])
def login_process():
    global displayerr
    email_or_username = request.form.get('email')
    password = request.form.get('password')
    conn = pymysql.connect(**db_config)
    cursor = conn.cursor()

    password_bytes = password.encode('utf-8')

    sql = """
    SELECT email, username, user_id, salt, password_hash, join_date FROM users WHERE email = %s
    """
    cursor.execute(sql, (email_or_username,))
    result = cursor.fetchone()
    if result == None:
        sql = """
        SELECT email, username, user_id, salt, password_hash, join_date FROM users WHERE username = %s
        """
        cursor.execute(sql, (email_or_username,))
        result = cursor.fetchone()

    if result == None:
        return redirect(url_for('login_page', err=1))
    
    salt = result[3]
    salt_bytes = salt.encode('utf-8')
    hashed_password = bcrypt.hashpw(password_bytes, salt_bytes)
    decoded_hash = hashed_password.decode('utf-8')


    if decoded_hash != result[4]:
        displayerr = True
        return redirect(url_for('login_page', err=2))
    else:
        session['user_id'] = result[2]
        session['username'] = result[1]
        session['join_date'] = result[5]


    return redirect(url_for('home'))


if __name__ == '__main__':
    if not os.path.exists(UPLOAD_FOLDER):
        os.makedirs(UPLOAD_FOLDER)  
    app.run(debug=True, host="0.0.0.0", port=5000)