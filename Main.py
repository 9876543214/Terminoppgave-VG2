#! C:\Program Files\Python312\python.exe

import os
from flask import Flask, request, redirect, url_for, render_template, send_from_directory, jsonify
import pymysql
from werkzeug.utils import secure_filename
from datetime import datetime
import bcrypt


app = Flask(__name__)

user_id = 1
errtrue = False

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
    global errtrue
    err = request.args.get('err', 0)
    if errtrue == True:
        errtrue = False
        return redirect(url_for('home'))
    
    if err != 0:
        errtrue = True

    conn = pymysql.connect(**db_config)
    cursor = conn.cursor(pymysql.cursors.DictCursor)  # vet ikke

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
    # database
    conn = pymysql.connect(**db_config)
    cursor = conn.cursor()

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
            INSERT INTO users (username, email, password_hash, join_date)
            VALUES (%s, %s, %s, %s)
            """
        cursor.execute(sql, (username, email, hashed_password, joindate))
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
    return render_template('login.html')


if __name__ == '__main__':
    if not os.path.exists(UPLOAD_FOLDER):
        os.makedirs(UPLOAD_FOLDER)  
    app.run(debug=True, host="0.0.0.0", port=5000)