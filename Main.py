#! C:\Program Files\Python312\python.exe

import os
from flask import Flask, request, redirect, url_for, render_template
import pymysql
from werkzeug.utils import secure_filename
from datetime import datetime

app = Flask(__name__)



@app.route('/')
def home():
    conn = pymysql.connect(**db_config)
    cursor = conn.cursor(pymysql.cursors.DictCursor)  # DictCursor returns results as dictionaries

    # Query to randomly select posts that are not marked as deleted
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

    return render_template('index.html', posts=posts)

user_id = 1

# Configure where uploaded media files will be stored
UPLOAD_FOLDER = 'static/uploads/'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'mp4', 'mov', 'avi'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

db_config = {
    'host': '10.2.3.235',
    'user': 'sosial',
    'password': 'sosial123',
    'db': 'sosial_media'
}

# function to check allowed file extensions
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Route to handle form submission
@app.route('/submit-post', methods=['POST'])
def submit_post():
    # Connect to the MariaDB database
    conn = pymysql.connect(**db_config)
    cursor = conn.cursor()

    # Get form data
    content = request.form.get('content')
    visibility = request.form.get('visibility')

    # Get current timestamp
    created_at = datetime.now()

    # Handle media upload if there's any
    media_path = None
    if 'media' in request.files:
        media_file = request.files['media']
        if media_file and allowed_file(media_file.filename):
            # Secure the filename and save the file to the UPLOAD_FOLDER
            filename = secure_filename(media_file.filename)
            
            media_file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            media_path = filename  # Save path for database

    # Insert the post data into the database
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
    return redirect(url_for('home'))


if __name__ == '__main__':
    if not os.path.exists(UPLOAD_FOLDER):
        os.makedirs(UPLOAD_FOLDER)  # Create the upload directory if it doesn't exist
    app.run(debug=True, host="0.0.0.0", port=5000)