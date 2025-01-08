#! C:\Program Files\Python312\python.exe

import os
from flask import Flask, request, redirect, url_for, render_template, send_from_directory, jsonify, session
import pymysql
from werkzeug.utils import secure_filename
from datetime import datetime
import bcrypt
import mimetypes

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
UPLOAD_FOLDER = r'\\10.2.3.235\sambashare' # Mappen som media blir lagret
ALLOWED_EXTENSIONS = {'jpeg', 'jpg', 'mpeg', 'mp4', 'mov', 'webm', 'gif', 'png', 'tiff', 'bmp', 'pdf', 'svg', 'webp', 'avif', 'avi'} # Tillatte filtyper å poste
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER #setter mappen som en variabel i app

# Sjekker om fil er gyldig filtype
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/')
def home():
    global displayerr
    global preverr_home
    err = request.args.get('err', 0) # Henter err kode, hvis ikke blir err = 0
    page = request.args.get('posts', "1")
    newpage = request.args.get('newpage', "0")
    
    if displayerr == False: 
        if preverr_home == err:
            preverr_home = None
            if str(newpage) == "0":
                return redirect(url_for('home'))# refresher url hvis error allerede er vist, så error ikke blir på skjermen
            
    preverr_home = err
    displayerr = False

    posts = fetch_posts(page)

    if 'user_id' in session and session['user_id'] is not None: # Sjekker om bruker er logget inn
        loggedin = "1"
    else: 
        loggedin = "2"

    try:
        files = os.listdir(UPLOAD_FOLDER) # Prøver å nå filmappe
    except Exception as e:
        print(f"Error reading shared folder: {e}")
        files = []

    return render_template('index.html', posts=posts, files=files, err=err, loggedin=loggedin, page=page) # Viser og sender data til html


@app.route('/media/<filename>')
def serve_file(filename): # hoster media på en url så hovedsiden kan hente 
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
    if 'user_id' not in session or session['user_id'] is None: # Sjekker om bruker er ligget inn før de får poste
        displayerr = True
        return redirect(url_for('home', err=2, posts=1))
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
        print(media_file)
        if media_file.filename:
            if media_file and allowed_file(media_file.filename): # Sjekker om filtype er tillatt
                
                filename = secure_filename(media_file.filename) # Fikser ugyldig filnavn for å unngå error
                
                media_file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                media_path = filename  # Lagrer filnavn til databasen
            else:
                displayerr = True
                return redirect(url_for('home', err=1, posts=1)) # Sender bruker tilbake hvis filtype ikke er tillatt
            

    # sett inn i databasen
    try:
        sql = """
            INSERT INTO posts (user_id, content, media_path, visibility, created_at)
            VALUES (%s, %s, %s, %s, %s)
        """
        cursor.execute(sql, (user_id, content, media_path, visibility, created_at,)) 
        conn.commit()
    except Exception as e:
        print(f"Error: {e}")
        conn.rollback()
    finally:
        cursor.close()
        conn.close()

    return redirect(url_for('home', err=0, posts=1))


@app.route('/register')
def registerpage(): # Viser register side
    return render_template('register.html') 

@app.route('/process-register', methods=['POST'])
def process_register():
    conn = pymysql.connect(**db_config)
    cursor = conn.cursor()
    username = request.form.get('username') # Henter nødvendig data
    email = request.form.get('email')
    password = request.form.get('password')
    joindate = datetime.now()
    password_bytes = password.encode('utf-8')


    salt = bcrypt.gensalt()

    hashed_password = bcrypt.hashpw(password_bytes, salt) #Hasher passord for tryggere lagring
    

    try:
        sql = """
            INSERT INTO users (username, email, password_hash, join_date, salt)
            VALUES (%s, %s, %s, %s, %s)
            """
        cursor.execute(sql, (username, email, hashed_password, joindate, salt,)) # Lagrer data i databasen
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


# @app.route('/validate_email')
# def validate_email():
#     email = request.args.get('email')
#     conn = pymysql.connect(**db_config) 
#     cursor = conn.cursor()

#     sql = """
#     SELECT email FROM users WHERE email = %s
#     """
#     cursor.execute(sql, (email,))
#     result = cursor.fetchone()

#     conn.close()

#     if result:
#         return jsonify({"exists": True, "email": result[0]})
#     else:
#         return jsonify({"exists": False})


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
    cursor.execute(sql, (email_or_username,)) # Sjekker om email finnes i databasen
    result = cursor.fetchone()
    if result == None: # Hvis den ikke fant email, leter den etter brukernavn
        sql = """
        SELECT email, username, user_id, salt, password_hash, join_date FROM users WHERE username = %s
        """
        cursor.execute(sql, (email_or_username,))
        result = cursor.fetchone()

    if result == None:
        conn.close()
        return redirect(url_for('login_page', err=1)) # Hvis email eller brukernavn ikke finnes, retuneres err 1
    
    salt = result[3]
    salt_bytes = salt.encode('utf-8')
    hashed_password = bcrypt.hashpw(password_bytes, salt_bytes)# Gjør dette passordet lik som den i databasen
    decoded_hash = hashed_password.decode('utf-8') 
    password = None # Tømmer ikke-hashed passord


    if decoded_hash != result[4]:
        displayerr = True
        return redirect(url_for('login_page', err=2)) # Hvis passord ikke er lik den i databasen, retuneres err 2
    else:
        session['user_id'] = result[2]
        session['username'] = result[1]
        session['join_date'] = result[5]

    conn.close()
    return redirect(url_for('home'))

@app.route('/signout')
def signout(): # Fjerner all login informasjon i session
    session.pop('user_id', None)
    session.pop('username', None)
    session.pop('join_date', None)
    return redirect(url_for('home'))



@app.route('/addlike')
def addlike(): # funksjon for å legge til og fjærne likes fra databasen
    conn = pymysql.connect(**db_config)
    cursor = conn.cursor(pymysql.cursors.DictCursor)
    post_id = request.args.get('post_id')
    if 'user_id' in session or session['user_id'] is not None: # Sjekker om bruker er logget inn
        user_id = session['user_id']
        sql = """
            SELECT * FROM likes where user_id = %s AND post_id = %s
        """
        cursor.execute(sql, (user_id, post_id,))
        result = cursor.fetchone() # Sjekker om bruker allerede har liket post

        if result == None: # Hvis ikke, legger til like i databasen
            sql2 = """
                INSERT INTO likes (user_id, post_id) VALUES (%s, %s)
            """
            try:
                cursor.execute(sql2, (user_id, post_id,))
                conn.commit()
                conn.close()
                return ("Liked")
            except:
                conn.close()
                print("error liking")  

        else: # Hvis bruker har liket, fjerner liket fra databasen
            sql3 = """
                DELETE FROM likes WHERE user_id = %s AND post_id = %s
            """
            cursor.execute(sql3, (user_id, post_id))
            conn.commit()
            conn.close()
            return ("Unliked")
        
@app.route('/opencomments')
def opencomments():
    conn = pymysql.connect(**db_config)
    cursor = conn.cursor(pymysql.cursors.DictCursor)
    post_id = request.args.get('post_id')
    sql = """
        SELECT * FROM comments WHERE post_id = %s
    """
    cursor.execute(sql, (post_id)) # Henter comments
    comments = cursor.fetchall()
    for comment in comments:# Henter brukernavn per comment
        user_id = comment['user_id']
        sql = """
            SELECT username FROM users WHERE user_id = %s
        """ 
        cursor.execute(sql, (user_id)) 
        username = cursor.fetchone()
        comment['username'] = username['username'] if username else "Unknown user" # Hvis feil, blir det ukjent bruker

    conn.close()
    return jsonify(comments)

@app.route('/submit_comment', methods=['POST'])
def submit_comment():
    conn = pymysql.connect(**db_config)
    cursor = conn.cursor(pymysql.cursors.DictCursor)
    comment_content = request.form.get('content') # henter publisert comment
    post_id = request.form.get('post_id')
    if 'user_id' in session and session['user_id'] is not None: # Sjekker om bruker er logget inn
        user_id = session['user_id']
        sql = """
            INSERT INTO comments (post_id, user_id, content) VALUES (%s, %s, %s)
        """
        cursor.execute(sql, (post_id, user_id, comment_content)) # Setter comment inn i databasen
        conn.commit()
        conn.close()
        return redirect(url_for('home'))
    else:
        conn.close()
        return jsonify("Not logged in")


def fetch_posts(selected_posts):
    conn = pymysql.connect(**db_config)
    cursor = conn.cursor(pymysql.cursors.DictCursor)

    # Velger posts 
    try:
        if str(selected_posts) == "1": # Sjekker hvilke posts bruker vil se. Enten alle, liked eller postet selv
            value = 'WHERE is_deleted = FALSE'
        elif str(selected_posts) == "2": # Henter posted selv
            if 'user_id' in session and session['user_id'] is not None: # Sjekker om bruker er logget inn
                value = "WHERE user_id = " + str(session['user_id'])
        elif str(selected_posts) == "3": # Henter liked posts
            sql = """
                SELECT post_id FROM likes WHERE user_id = %s
            """
            if 'user_id' in session or session['user_id'] is not None: # Sjekker om bruker er logget inn
                cursor.execute(sql, (session['user_id']))
            else: 
                return redirect(url_for('home'))
            liked_posts = cursor.fetchall()
            liked_posts = [row['post_id'] for row in liked_posts] # Henter post id for alle liked post
            print(liked_posts)
            value = 'WHERE post_id IN ({})'.format(', '.join(map(str, liked_posts)))
            print(value)

        sql = """
            SELECT post_id, user_id, content, media_path, created_at, visibility, like_count, comment_count
            FROM posts
            {value} ORDER BY created_at DESC LIMIT 100
        """.format(value=value) # Henter valgte posts
        cursor.execute(sql,)
        posts = cursor.fetchall() 
        for post in posts: #Henter brukernavn per post
            user_id = post['user_id']
            sql = """
                SELECT username 
                FROM users
                WHERE user_id = %s
            """
            cursor.execute(sql, (user_id,)) # Henter brukernavn
            user = cursor.fetchone()    
            post_id = post['post_id']
            
            if 'user_id' in session:
                if session['user_id'] is not None: # Sjekker om bruker er loggget inn
                    user_id2 = session['user_id']
                    sql = """
                        SELECT * FROM likes WHERE post_id = %s AND user_id = %s
                    """
                    cursor.execute(sql, (post_id, user_id2,)) # Sjekker om bruker liker post
                    userliked = cursor.fetchone()
                    post['userliked'] = userliked
                else:
                    post['userliked'] = None # Hvis bruker ikke er logget inn, liker ikke bruker post
            else:
                post['userliked'] = None
            sql = """
                SELECT * FROM likes WHERE post_id = %s
            """
            cursor.execute(sql, (post_id,)) # Sjekker antall likes
            likes = cursor.fetchall()
            post['likes'] = len(likes)
            sql = """
                SELECT post_id FROM comments WHERE post_id = %s
            """
            cursor.execute(sql, (post_id,)) # Sjekker antall comments
            comments = cursor.fetchall() 
            post['comments'] = len(comments) # Legger inn data i post
            username = user['username']
            post['username'] = username
            date = post['created_at'].strftime("%b %d")
            post['date'] = date 
            if post['media_path'] != None: # Sjekker om post har media
                mime_type, _ = mimetypes.guess_type(post['media_path']) # Finner filtype
                if mime_type:
                    if mime_type.startswith('image/'):
                        if mime_type == 'image/gif':
                            filetype = 'GIF' #Setter filtype som gif
                        else:
                            filetype = 'Image' # Setter filtype som bilde
                    elif mime_type.startswith('video/'):
                        filetype = 'Video' # Setter filtype som video
                post['filetype'] = filetype

    except Exception as e:
        print(f"Error: {e}")
        posts = []
    finally:
        cursor.close()
        conn.close()

    return posts

if __name__ == '__main__':
    app.run(debug=True, host="0.0.0.0", port=5000)