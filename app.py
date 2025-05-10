from flask import Flask, render_template, request, redirect, session
from flask import url_for, flash, session, g, jsonify
import sqlite3
import os
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from flask import Blueprint
from flask_cors import CORS
from datetime import datetime, timedelta, timezone

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'dev‐only‐change‐me')


# INITIAL DATABASE SET UP
DB_FILE = 'calefamily.db'

# Path to your SQLite file
DB_FILE = os.path.join(os.path.dirname(__file__), 'calefamily.db')

def get_db():
    """
    Returns a sqlite3.Connection, stored on flask.g for reuse per request.
    """
    if 'db' not in g:
        g.db = sqlite3.connect(DB_FILE)
        g.db.row_factory = sqlite3.Row
    return g.db

@app.teardown_appcontext
def close_db(e=None):
    """
    Closes the database at the end of the request.
    """
    db = g.pop('db', None)
    if db is not None:
        db.close()

# Helper to execute queries
def query_db(query, args=(), one=False):
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    cur.execute(query, args)
    rv = cur.fetchall()
    conn.commit()
    conn.close()
    return (rv[0] if rv else None) if one else rv

# Ensure database exists
def init_db():
    if not os.path.exists(DB_FILE):
        conn = sqlite3.connect(DB_FILE)
        c = conn.cursor()
        c.execute('''
            CREATE TABLE users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL UNIQUE,
                password TEXT NOT NULL
            )
        ''')
        c.execute('''
            CREATE TABLE posts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                subcale_name TEXT,
                content TEXT NOT NULL,
                FOREIGN KEY(user_id) REFERENCES users(id)
            )
        ''')
        c.execute('''
            CREATE TABLE comments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                post_id INTEGER,
                user_id INTEGER,
                subcale_name TEXT,
                content TEXT NOT NULL,
                comment TEXT NOT NULL,
                hearts INTEGER DEFAULT 0,
                laughs INTEGER DEFAULT 0,
                notes INTEGER DEFAULT 0,
                thumbs INTEGER DEFAULT 0,
                comment_id INTEGER,
                reaction TEXT,
                FOREIGN KEY(post_id) REFERENCES posts(id),
                FOREIGN KEY(comment_id) REFERENCES comments(id),
                FOREIGN KEY(user_id) REFERENCES users(id)
            )
        ''')
        c.execute('''
            CREATE TABLE reactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                post_id INTEGER,
                comment_id INTEGER,
                user_id INTEGER,
                reaction TEXT,
                FOREIGN KEY(post_id) REFERENCES posts(id),
                FOREIGN KEY(comment_id) REFERENCES comments(id),
                FOREIGN KEY(user_id) REFERENCES users(id)
            )
        ''')
        c.execute('''
            CREATE TABLE messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                sender_id INTEGER,
                recipient_id INTEGER,
                content TEXT NOT NULL,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                is_read INTEGER DEFAULT 0,
                deleted INTEGER DEFAULT 0,
                FOREIGN KEY(sender_id) REFERENCES users(id),
                FOREIGN KEY(recipient_id) REFERENCES users(id)
            )
        ''')
        conn.commit()
        conn.close()


# SECURITY 
# Password hashing helpers
def hash_password(password):
    return generate_password_hash(password)

def check_password(password, hashed):
    return check_password_hash(hashed, password)


# REGISTRATION
# Notification helper
def notify_user(recipient_id, message, notif_type='registration'):
    # If the payload is just a string, treat it as a normal notification
    if isinstance(message, str) or notif_type != 'registration':
        db = get_db()
        db.execute(
            "INSERT INTO notifications (recipient, type, payload) VALUES (?, ?, ?)",
            (recipient_id, notif_type, message)
        )
        db.commit()
        return

    # Otherwise, it’s a structured registration request
    approve_url = url_for('admin.approve_registration', user_id=message['pending_id'])
    deny_url    = url_for('admin.deny_registration',    user_id=message['pending_id'])
    content = (
      f"New registration request: <b>{message['username']}</b><br>"
      f"<a href='{approve_url}'>✅ Approve</a> | "
      f"<a href='{deny_url}'>❌ Deny</a>"
    )
    db = get_db()
    db.execute(
        "INSERT INTO messages (sender_id, recipient_id, content) VALUES (?, ?, ?)",
        (0, recipient_id, content)
    )
    db.commit()

# Register
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        # 1) Extract & sanitize inputs
        username = request.form.get('username', '').strip()
        first    = request.form.get('first',    '').strip()
        last     = request.form.get('last',     '').strip()
        password = request.form.get('password', '')
        confirm  = request.form.get('confirm',  '')

        # 2) Basic validation
        if not (username and first and last and password and confirm):
            flash('All fields are required.', 'error')
            return redirect(url_for('register'))

        if password != confirm:
            flash('Passwords do not match.', 'error')
            return redirect(url_for('register'))

        # Enforce only a 4‑character minimum
        if len(password) < 4:
            flash('Password must be at least 4 characters long.', 'error')
            return redirect(url_for('register'))

        if password != confirm:
            flash('Passwords do not match.', 'error')
            return redirect(url_for('register'))

        # 3) Uniqueness check
        existing = query_db(
            "SELECT id FROM users WHERE username = ?",
            (username,),
            one=True
        )
        if existing:
            flash('That username is already taken.', 'error')
            return redirect(url_for('register'))

        # 4) Hash & insert pending user
        pw_hash = hash_password(password)
        query_db(
            """
            INSERT INTO users
              (username, password, first, last, is_approved)
            VALUES
              (?,        ?,        ?,     ?,    0)
            """,
            (username, pw_hash, first, last)
        )

        # 5) Grab the new user's id
        new_user = query_db(
            "SELECT id FROM users WHERE username = ?",
            (username,),
            one=True        
        )
        user_id = new_user['id']

        # 6) Notify all admins
        admins = query_db("SELECT id FROM users WHERE is_admin = 1")
        new_user = {'pending_id': user_id, 'username': username, 'First': first, 'Last': last,  }
        for a in admins:
            #print(f"DEBUG register → notifying admin_id={a['id']} about new user {username}")
            notify_user(
                a['id'],new_user, notif_type='registration')
        #print("DEBUG register → done notify_user calls")
        flash('Registration submitted and pending approval.', 'info')
        return redirect(url_for('login'))

    # GET request just renders the form
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username','').strip()
        password = request.form.get('password','')

        # Fetch the user row
        user = query_db(
            "SELECT * FROM users WHERE username = ?",
            (username,),
            one=True
        )

        # 1) No such user?
        if not user:
            flash('Invalid username or password.', 'error')
            return redirect(url_for('login'))

        # 2) Check the password hash
        stored_hash = user['password']            # direct indexing
        if not check_password_hash(stored_hash, password):
            flash('Invalid username or password.', 'error')
            return redirect(url_for('login'))

        # 3) Check approval flag
        if not user['is_approved']:               # direct indexing
            flash('Your account is still pending approval.', 'info')
            return redirect(url_for('login'))

        # 4) All good — log them in
        session.clear()
        session['user_id'] = user['id']
        session['username'] = user['username']
        flash('Logged in successfully!', 'success')
        return redirect(url_for('home'))

    # GET → render the form
    return render_template('login.html')

# Logout
@app.route('/logout')
def logout():
    # Clear the session (logs the user out)
    session.clear()
    flash('You have been logged out.', 'info')
    return redirect(url_for('login'))

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

@admin_bp.route('/registrations')
def view_registrations():
    pending = query_db("SELECT * FROM users WHERE is_approved = 0")
    return render_template('admin_registrations.html', users=pending)

@admin_bp.route('/registrations/<int:user_id>/approve')
def approve_registration(user_id):
    query_db("UPDATE users SET is_approved = 1 WHERE id = ?", (user_id,))
    notify_user(user_id, 'Your account has been approved!')
    flash('User approved.', 'success')
    return redirect(url_for('admin.view_registrations'))

@admin_bp.route('/registrations/<int:user_id>/deny')
def deny_registration(user_id):
    query_db("DELETE FROM users WHERE id = ?", (user_id,))
    flash('User denied and removed.', 'info')
    return redirect(url_for('admin.view_registrations'))

# Register blueprint
app.register_blueprint(admin_bp)


# SITES
# Home page
@app.route('/')
def home():
    # 1 Existing subcales
    subcales = [
        {'name': 'Caleducation', 'emoji': '📚'},
        {'name': 'Calecho', 'emoji': '🎵'},
        {'name': 'Calentertainment', 'emoji': '🎬'},
        {'name': 'Calexplore', 'emoji': '🌎'},
        {'name': 'Calenrichment', 'emoji': '🎨'},
        {'name': 'Calespañol', 'emoji': '🗣️'}
    ]
    # 2) Default unread‑message count
    unread_count = 0

    # 3) If logged in, open the DB and count unread messages
    user_id = session.get('user_id')
    users = []
    if user_id:
        conn = sqlite3.connect('calefamily.db')
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        # Count unread messages
        cursor.execute(
            """
            SELECT COUNT(*) 
              FROM messages 
             WHERE recipient_id = ? 
               AND is_read      = 0 
               AND deleted      = 0
               AND message_type = 'mail'
            """,
            (user_id,)
        )
        unread_count = cursor.fetchone()[0] or 0

        # Fetch all other users and their last_seen
        cursor.execute("SELECT id, username, last_seen FROM users")
        rows = cursor.fetchall()
        for row in rows:
            status = get_user_status(row['last_seen'])
            users.append({'id': row['id'], 'username': row['username'], 'status': status})
        conn.close()

    # 4) Render with the unread_count in your context
    for row in rows:
        status = get_user_status(row['last_seen'])
        print(f"[DEBUG] User {row['username']} last seen {row['last_seen']} → status {status}")
        users.append({'id': row['id'], 'username': row['username'], 'status': status})
    return render_template(
        'home.html',
        subcales=subcales,
        unread_count=unread_count,
        users=users
    )

# Subcale page
@app.route('/subcale/<subcale_name>', methods=['GET', 'POST'])
def subcale(subcale_name, **kwargs):
        # 1 Existing subcales
    subcales = [
        {'name': 'Caleducation', 'emoji': '📚'},
        {'name': 'Calecho', 'emoji': '🎵'},
        {'name': 'Calentertainment', 'emoji': '🎬'},
        {'name': 'Calexplore', 'emoji': '🌎'},
        {'name': 'Calenrichment', 'emoji': '🎨'},
        {'name': 'Calespañol', 'emoji': '🗣️'}
    ]
    
    #print("SESSION DUMP:", dict(session))
    if 'user_id' not in session:
        return redirect('/login')

    conn = sqlite3.connect('calefamily.db')
    c = conn.cursor()

    if request.method == 'POST':
        content = request.form['content']
        c.execute('INSERT INTO posts (user_id, subcale_name, content) VALUES (?, ?, ?)',
                  (session['user_id'], subcale_name, content))
        conn.commit()
        conn.close()
        return redirect(url_for('subcale', subcale_name=subcale_name))

    # Fetch posts WITH REACTION COUNTS (added hearts, laughs, notes, thumbs)
    c.execute('''
        SELECT posts.id, users.username, posts.content, 
               posts.hearts, posts.laughs, posts.notes, posts.thumbs
        FROM posts 
        JOIN users ON posts.user_id = users.id 
        WHERE subcale_name = ?
    ''', (subcale_name,))
    
    posts = c.fetchall()

    # Fetch comments for each post (unchanged)
    posts_with_comments = []
    for post in posts:
        #print("DEBUG >> session username:", session.get('username'), "| post author:", post[1])
        post_id = post[0]
        c.execute('''
            SELECT users.username, comments.comment, comments.id, 
                   comments.hearts, comments.laughs, comments.notes, comments.thumbs
            FROM comments
            JOIN users ON comments.user_id = users.id
            WHERE post_id = ?
        ''', (post_id,))
        comments = c.fetchall()
        # Include all post fields (id, username, content, hearts, laughs, notes, thumbs) + comments
        posts_with_comments.append((post[0], post[1], post[2], post[3], post[4], post[5], post[6], comments))

    conn.close()

    # Dynamically select template
    template_file = f"{subcale_name.lower()}.html"
    # Use app.template_folder if set, else default to 'templates'
    template_folder = app.template_folder if app.template_folder else os.path.join(os.path.dirname(__file__), 'templates')
    template_path = os.path.join(template_folder, template_file)
    if not os.path.exists(template_path):
        template_file = "subcale.html"

    # Default unread‑message count
    unread_count = 0

    # 3) If logged in, open the DB and count unread messages
    user_id = session.get('user_id')
    if user_id:
        conn = sqlite3.connect('calefamily.db')
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT COUNT(*) 
              FROM messages 
             WHERE recipient_id = ? 
               AND is_read      = 0 
               AND deleted      = 0
               AND message_type = 'mail'
            """,
            (user_id,)
        )
        # fetchone()[0] yields the integer count
        unread_count = cursor.fetchone()[0] or 0

    if subcale_name.lower() == 'caleducation':
        try:
            with open("static/featured_fact.txt", "r", encoding="utf-8") as f:
                kwargs['featured_fact'] = f.read()
        except FileNotFoundError:
            kwargs['featured_fact'] = "Today's featured fact is not available."

    if subcale_name.lower() == 'calentertainment':
        try:
            with open("static/movie_plot.txt", "r", encoding="utf-8") as f:
                kwargs['plot_movie'] = f.read()
        except FileNotFoundError:
            kwargs['plot_movie'] = "Today's movie is not available."    

    return render_template(template_file, 
                           subcale_name=subcale_name, 
                           posts=posts_with_comments, 
                           current_user=session.get('username'),
                           subcales=subcales,
                           unread_count=unread_count,
                           **kwargs)

# Each subcale html definition

@app.route('/calecho')
def calecho():
    return subcale('calecho')

@app.route('/calexplore')
def calexplore():
    return subcale('calexplore')

@app.route('/caleducation')
def caleducation():
    try:
        with open("static/featured_fact.txt", "r", encoding="utf-8") as f:
            fact_text = f.read()
    except FileNotFoundError:
        fact_text = "Today's featured fact is not available."

    #print("📘 DEBUG featured_fact preview:", fact_text[:150])  # print a preview

    return subcale('caleducation', featured_fact=fact_text)


@app.route('/calenrichment')
def calenrichment():
    return subcale('calenrichment')

@app.route('/calentertainment')
def calentertainment():
    try:
        with open("static/movie_plot.txt", "r", encoding="utf-8") as f:
            plot_text = f.read()
    except FileNotFoundError:
        plot_text = "Today's movie is not available."

    #print("📘 DEBUG featured_fact preview:", fact_text[:150])  # print a preview

    return subcale('calentertainment', plot_movie=plot_text)



@app.route('/calespanol')
def calespanol():
    return subcale('calespanol')

# POSTING & COMMENTING
# Edit post
@app.route('/edit_post/<int:post_id>', methods=['GET', 'POST'])
def edit_post(post_id):
    if 'user_id' not in session:
        return redirect('/login')

    conn = sqlite3.connect('calefamily.db')
    c = conn.cursor()

    if request.method == 'POST':
        new_content = request.form['content']
        c.execute('UPDATE posts SET content = ? WHERE id = ? AND user_id = ?', 
                  (new_content, post_id, session['user_id']))
        conn.commit()
        conn.close()
        return redirect(f'/subcale/{request.args.get("subcale_name")}')
    
    # Fetch the existing post content to pre-populate the form
    c.execute('SELECT content FROM posts WHERE id = ? AND user_id = ?', (post_id, session['user_id']))
    post = c.fetchone()
    conn.close()

    if not post:
        return "Post not found or not authorized to edit this post."

    return render_template('edit_post.html', post_id=post_id, content=post[0])

# Delete post
@app.route('/delete_post/<int:post_id>', methods=['POST'])
def delete_post(post_id):
    if 'user_id' not in session:
        return redirect('/login')

    conn = sqlite3.connect('calefamily.db')
    c = conn.cursor()

    # Delete the post
    c.execute('DELETE FROM posts WHERE id = ? AND user_id = ?', (post_id, session['user_id']))
    conn.commit()
    conn.close()

    return redirect(f'/subcale/{request.args.get("subcale_name")}')

# Add comment to a post
@app.route('/add_comment/<int:post_id>', methods=['POST'])
def add_comment(post_id):
    if 'user_id' not in session:
        return redirect('/login')

    comment_text = request.form['comment']
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute('INSERT INTO comments (post_id, user_id, comment) VALUES (?, ?, ?)',
              (post_id, session['user_id'], comment_text))
    conn.commit()
    conn.close()
    return redirect(request.referrer)

# Edit comment
@app.route('/edit_comment/<int:comment_id>', methods=['GET', 'POST'])
def edit_comment(comment_id):
    if 'user_id' not in session:
        return redirect('/login')

    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()

    # Get post_id and subcale_name for redirect
    c.execute('''
        SELECT posts.subcale_name 
        FROM comments
        JOIN posts ON comments.post_id = posts.id
        WHERE comments.id = ?
    ''', (comment_id,))
    result = c.fetchone()
    if not result:
        conn.close()
        return "Comment not found."
    subcale_name = result[0]

    if request.method == 'POST':
        new_comment = request.form.get('comment')
        if not new_comment:
            conn.close()
            return "Comment cannot be empty.", 400

        c.execute('''
            UPDATE comments 
            SET comment = ? 
            WHERE id = ? AND user_id = ?
        ''', (new_comment, comment_id, session['user_id']))
        conn.commit()
        conn.close()
        return redirect(url_for('subcale', subcale_name=subcale_name))  # Redirect back to subcale

    # GET request - fetch comment content
    c.execute('''
        SELECT comment 
        FROM comments 
        WHERE id = ? AND user_id = ?
    ''', (comment_id, session['user_id']))
    comment = c.fetchone()
    conn.close()

    if not comment:
        return "Comment not found or not authorized."

    return render_template(
        'edit_comment.html',
        comment_id=comment_id,
        comment=comment[0],
        subcale_name=subcale_name  # Pass subcale_name to template
    )

# Delete a comment
@app.route('/delete_comment/<int:comment_id>')
def delete_comment(comment_id):
    if 'user_id' not in session:
        return redirect('/login')

    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()

    # Check if the user owns the comment
    c.execute('SELECT user_id FROM comments WHERE id = ?', (comment_id,))
    result = c.fetchone()
    if result and result[0] == session['user_id']:
        c.execute('DELETE FROM comments WHERE id = ?', (comment_id,))
        conn.commit()

    conn.close()
    return redirect(request.referrer)

# Reactions
@app.route('/react/<int:post_id>/<reaction>', methods=['POST'])
def react(post_id, reaction):
    if 'user_id' not in session:
        return redirect('/login')

    # Check if the reaction is for a comment
    comment_id = request.form.get('comment_id')

    conn = sqlite3.connect('calefamily.db')
    c = conn.cursor()

    # If it's a comment reaction
    if comment_id:
        c.execute('SELECT * FROM reactions WHERE comment_id = ? AND user_id = ?', (comment_id, session['user_id']))
    else:
        # If it's a post reaction
        c.execute('SELECT * FROM reactions WHERE post_id = ? AND user_id = ?', (post_id, session['user_id']))

    existing_reaction = c.fetchone()

    if existing_reaction:
        return redirect(request.referrer)  # Don't allow multiple reactions from the same user

    # Update the reaction count for the post or comment
    if comment_id:
        if reaction == 'heart':
            c.execute('UPDATE comments SET hearts = hearts + 1 WHERE id = ?', (comment_id,))
        elif reaction == 'laugh':
            c.execute('UPDATE comments SET laughs = laughs + 1 WHERE id = ?', (comment_id,))
        elif reaction == 'note':
            c.execute('UPDATE comments SET notes = notes + 1 WHERE id = ?', (comment_id,))
        elif reaction == 'thumb':
            c.execute('UPDATE comments SET thumbs = thumbs + 1 WHERE id = ?', (comment_id,))
    else:
        if reaction == 'heart':
            c.execute('UPDATE posts SET hearts = hearts + 1 WHERE id = ?', (post_id,))
        elif reaction == 'laugh':
            c.execute('UPDATE posts SET laughs = laughs + 1 WHERE id = ?', (post_id,))
        elif reaction == 'note':
            c.execute('UPDATE posts SET notes = notes + 1 WHERE id = ?', (post_id,))
        elif reaction == 'thumb':
            c.execute('UPDATE posts SET thumbs = thumbs + 1 WHERE id = ?', (post_id,))

    # Insert the user's reaction to track that they have reacted
    if comment_id:
        c.execute('INSERT INTO reactions (post_id, comment_id, user_id, reaction) VALUES (?, ?, ?, ?)', 
                  (post_id, comment_id, session['user_id'], reaction))
    else:
        c.execute('INSERT INTO reactions (post_id, user_id, reaction) VALUES (?, ?, ?)', 
                  (post_id, session['user_id'], reaction))

    conn.commit()
    conn.close()

    return redirect(request.referrer)


# PROFILES
@app.route('/profile')
def profile():
    if 'user_id' not in session:
        return redirect('/login')
    
    conn = sqlite3.connect('calefamily.db')
    c = conn.cursor()
    c.execute('SELECT id, username, profile_pic, zodiac_sign, birth_year, favorite_color, favorite_animal, favorite_subject, favorite_hobby, favorite_movie, favorite_book FROM users WHERE id = ?', (session['user_id'],))
    user = c.fetchone()

    # Get unread message count
    c.execute('''
        SELECT COUNT(*) FROM messages
        WHERE recipient_id = ? AND is_read = 0 AND message_type = 'mail'
    ''', (session['user_id'],))
    unread_count = c.fetchone()[0]
    conn.close()

    return render_template('profile.html', user=user, unread_count=unread_count)

@app.route('/edit_profile', methods=['GET', 'POST'])
def edit_profile():
    if 'user_id' not in session:
        return redirect('/login')
    
    conn = sqlite3.connect('calefamily.db')
    c = conn.cursor()

    if request.method == 'POST':
        profile_pic = request.form['profile_pic']
        zodiac_sign = request.form['zodiac_sign']
        birth_year = request.form['birth_year']
        favorite_color = request.form['favorite_color']
        favorite_animal = request.form['favorite_animal']
        favorite_subject = request.form['favorite_subject']
        favorite_hobby = request.form['favorite_hobby']
        favorite_movie = request.form['favorite_movie']
        favorite_book = request.form['favorite_book']

        c.execute('''
            UPDATE users SET profile_pic = ?, zodiac_sign = ?, birth_year = ?, favorite_color = ?, 
            favorite_animal = ?, favorite_subject = ?, favorite_hobby = ?, favorite_movie = ?, favorite_book = ?
            WHERE id = ?
        ''', (profile_pic, zodiac_sign, birth_year, favorite_color, favorite_animal, favorite_subject, favorite_hobby, favorite_movie, favorite_book, session['user_id']))

        conn.commit()
        conn.close()
        return redirect('/profile')

    # Get current user info
    c.execute('SELECT profile_pic, zodiac_sign, birth_year, favorite_color, favorite_animal, favorite_subject, favorite_hobby, favorite_movie, favorite_book FROM users WHERE id = ?', (session['user_id'],))
    user = c.fetchone()
    conn.close()
    
    return render_template('edit_profile.html', user=user)

@app.route('/calengineers')
def calengineers():
    if 'user_id' not in session:
        return redirect('/login')

    conn = sqlite3.connect('calefamily.db')
    c = conn.cursor()
    c.execute('SELECT id, username FROM users')
    users = c.fetchall()
    conn.close()

    return render_template('calengineers.html', users=users)

@app.route('/user_profile/<int:user_id>')
def user_profile(user_id):
    if 'user_id' not in session:
        return redirect('/login')

    # Fetch the user's profile details
    conn = sqlite3.connect('calefamily.db')
    c = conn.cursor()
    c.execute('''
        SELECT id, username, profile_pic, zodiac_sign, birth_year, favorite_color, 
               favorite_animal, favorite_subject, favorite_hobby, favorite_movie, favorite_book 
        FROM users 
        WHERE id = ?
    ''', (user_id,))
    user = c.fetchone()
    conn.close()

    # If the user doesn't exist or the session doesn't match, redirect
    if not user:
        return "User not found"
    
    return render_template('user_profile.html', user=user)


# MAILBOX
@app.route('/send/<int:recipient_id>', methods=['GET', 'POST'])
def send_messages(recipient_id):
    conn = sqlite3.connect('calefamily.db')
    c = conn.cursor()

    # Optional: fetch original message if this is a reply
    original_message_content = request.args.get('original')

    if request.method == 'POST':
        content = request.form['message_content']
        sender_id = session['user_id']  # Assuming you store the current user in session

        # Get recipient info (we assume recipient_id is passed in the URL)
        recipient_id = recipient_id  # It's passed directly as part of the route, no need to fetch username

        # Insert the new message into the database
        c.execute('''
            INSERT INTO messages (sender_id, recipient_id, content, timestamp, message_type)
            VALUES (?, ?, ?, ?, 'mail')
        ''', (sender_id, recipient_id, content, datetime.now()))

        conn.commit()
        return redirect(url_for('send_messages', recipient_id=recipient_id))

    # Get sent messages (sent by the current user to this recipient)
    c.execute('''
        SELECT u.username, m.content, m.timestamp
        FROM messages m
        JOIN users u ON m.sender_id = u.id
        WHERE m.sender_id = ? AND m.recipient_id = ?
        ORDER BY m.timestamp DESC
    ''', (session['user_id'], recipient_id))
    messages = c.fetchall()

    # Get recipient username
    c.execute('SELECT username FROM users WHERE id = ?', (recipient_id,))
    recipient = c.fetchone()
    if recipient:
        recipient_username = recipient[0]
    else:
        return "Recipient not found", 404

    return render_template('send_messages.html',
                           messages=messages,
                           recipient=recipient_username,
                           recipient_id=recipient_id,
                           original_message_content=original_message_content)

@app.route('/sent_messages')
def sent_messages():
    user_id = session.get('user_id')
    if not user_id:
        return redirect(url_for('login'))

    db = get_db()
    sent = query_db(
        """
        SELECT
          m.id,
          u.username     AS recipient,
          m.content,
          m.timestamp
        FROM messages m
        JOIN users u ON m.recipient_id = u.id
        WHERE m.sender_id = ? AND m.deleted = 0
        ORDER BY m.timestamp DESC
        """,
        (user_id,)
    )
    return render_template('sent_messages.html', messages=sent)

@app.route('/inbox')
def inbox():
    user_id = session.get('user_id')
    if not user_id:
        return redirect(url_for('login'))

    # Open the DB and request dict‑like rows
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    c = conn.cursor()

    # 1) Fetch rows
    c.execute("""
        SELECT
        m.id,
        COALESCE(u.username, 'System') AS sender,
        m.content,
        m.timestamp,
        m.is_read
        FROM messages m
        LEFT JOIN users u 
        ON m.sender_id = u.id
        WHERE m.recipient_id = ?
        AND m.deleted      = 0
        AND m.message_type = 'mail'
        ORDER BY m.timestamp DESC
    """, (user_id,))

    rows = c.fetchall()              # this is a list of sqlite3.Row

    # 2) Convert each row into a plain dict
    messages = [dict(r) for r in rows]

    # 3) Count unread for badge
    c.execute("""
        SELECT COUNT(*) AS cnt
          FROM messages
         WHERE recipient_id = ?
           AND is_read      = 0
           AND deleted      = 0
           AND message_type = 'mail'
    """, (user_id,))
    unread_count = c.fetchone()['cnt']

    conn.close()

    # (Optional) debug to terminal
    #print(f"DEBUG inbox: {len(messages)} messages →", messages)

    # 4) Render template with a list of dicts
    return render_template(
        'inbox.html',
        messages=messages,
        unread_count=unread_count
    )

@app.route('/message/<int:message_id>/delete')
def delete_message(message_id):
    db = get_db()
    db.execute("UPDATE messages SET deleted = 1 WHERE id = ?", (message_id,))
    db.commit()
    return redirect(url_for('inbox'))

@app.route('/deleted_messages')
def deleted_messages():
    user_id = session.get('user_id')
    if not user_id:
        return redirect(url_for('login'))

    db = get_db()
    deleted = query_db(
        """
        SELECT
          m.id,
          u.username   AS sender,
          m.content,
          m.timestamp
        FROM messages m
        JOIN users u ON m.sender_id = u.id
        WHERE m.recipient_id = ? AND m.deleted = 1
        ORDER BY m.timestamp DESC
        """,
        (user_id,)
    )
    return render_template('deleted_messages.html', messages=deleted)

@app.route('/mark_as_read/<int:message_id>')
def mark_as_read(message_id):
    if 'user_id' not in session:
        return redirect('/login')

    conn = sqlite3.connect('calefamily.db')
    c = conn.cursor()
    c.execute('UPDATE messages SET is_read = 1 WHERE id = ? AND recipient_id = ?', 
             (message_id, session['user_id']))
    conn.commit()
    conn.close()
    
    return redirect(url_for('inbox'))

@app.route('/respond/<int:message_id>', methods=['GET', 'POST'])
def respond_to_message(message_id):
    conn = sqlite3.connect('calefamily.db')
    conn.row_factory = sqlite3.Row  # Add this line
    c = conn.cursor()

    # Get the original message
    c.execute("SELECT * FROM messages WHERE id = ?", (message_id,))
    original = c.fetchone()

    if request.method == 'POST':
        #response_text = request.form['response']
        response_text = request.form['message_content']
        sender_id = original['recipient_id']  # The original recipient becomes the sender
        recipient_id = original['sender_id']  # The original sender becomes the recipient

        c.execute('''
        INSERT INTO messages (sender_id, recipient_id, content, is_read, message_type)
        VALUES (?, ?, ?, 0, 'mail')
        ''', (sender_id, recipient_id, response_text))

        conn.commit()  # Use conn not db
        return redirect(url_for('inbox'))

    return render_template('respond.html', message=original)


# CHAT
CORS(app)

@app.route('/api/messages', methods=['GET'])
def get_messages():
    user_id = session.get('user_id')
    other_id = request.args.get('other_id')

    conn = get_db()
    cur = conn.cursor()
    # Fetch messages between user_id and other_id
    cur.execute("""
        SELECT m.*, u.username
        FROM messages m
        JOIN users u ON m.sender_id = u.id
        WHERE ((m.sender_id = ? AND m.recipient_id = ?) OR (m.sender_id = ? AND m.recipient_id = ?))
          AND m.message_type = 'chat'
        ORDER BY m.timestamp ASC
    """, (user_id, other_id, other_id, user_id))

    messages = [
        {
            'id': row[0],
            'sender_id': row[1],
            'recipient_id': row[2],
            'content': row[3],
            'timestamp': row[4],
            'is_read': bool(row[5]),
            'sender_name': row[8]  # username from joined users table
        } for row in cur.fetchall()
    ]

    # Mark unread messages from other_id to user_id as read (for chat messages)
    cur.execute("""
        UPDATE messages
        SET is_read = 1
        WHERE sender_id = ? AND recipient_id = ? AND message_type = 'chat' AND is_read = 0
    """, (other_id, user_id))
    conn.commit()

    # --- Add: Unread counts for all users except current chat ---
    # For the current user, count unread chat messages from each other user (excluding current chat)
    cur.execute("""
        SELECT sender_id, COUNT(*) as unread_count
        FROM messages
        WHERE recipient_id = ?
          AND is_read = 0
          AND message_type = 'chat'
        GROUP BY sender_id
    """, (user_id,))
    unread_counts = {row[0]: row[1] for row in cur.fetchall()}

    return jsonify({'messages': messages, 'unread_counts': unread_counts})

@app.route('/api/messages', methods=['POST'])
def send_message():
    user_id = session.get('user_id')
    data = request.get_json()
    recipient_id = data.get('recipient_id')
    content = data.get('content')

    #print("DEBUG send_message → user_id:", user_id)
    #print("DEBUG send_message → recipient_id:", recipient_id)
    #print("DEBUG send_message → content:", content)

    if not user_id or not recipient_id or not content:
        return jsonify({'error': 'Missing data'}), 400

    conn = get_db()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO messages (sender_id, recipient_id, content, message_type)
        VALUES (?, ?, ?, 'chat')
    """, (user_id, recipient_id, content))
    conn.commit()

    return jsonify({'success': True})

@app.route('/api/users')
def get_users():
    user_id = session.get('user_id')  # current user
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT id, username, last_seen FROM users WHERE id != ?", (user_id,))
    users = []
    for row in cur.fetchall():
        status = get_user_status(row['last_seen'])
        users.append({'id': row['id'], 'username': row['username'], 'status': status})
    return jsonify(users)

# Last Seen
def get_user_status(last_seen):
    if not last_seen:
        return 'offline'
    try:
        last_seen_dt = datetime.fromisoformat(last_seen)
        # Ensure last_seen_dt is timezone-aware; if not, assume UTC
        if last_seen_dt.tzinfo is None:
            last_seen_dt = last_seen_dt.replace(tzinfo=timezone.utc)
    except ValueError:
        return 'offline'
    now = datetime.now(timezone.utc)
    delta = now - last_seen_dt
    if delta < timedelta(seconds=60):
        return 'online'
    elif delta < timedelta(minutes=2):
        return 'recently-online'
    return 'offline'


@app.route('/update_last_seen', methods=['POST'])
def update_last_seen():
    user_id = session.get('user_id')
    if not user_id:
        return '', 401

    now = datetime.now(timezone.utc).isoformat()
    #print(f"[DEBUG] Updating last_seen for user_id={user_id} → {now}")

    db = get_db()
    # Safety check: ensure user exists before updating
    user = db.execute("SELECT id FROM users WHERE id = ?", (user_id,)).fetchone()
    if not user:
        return '', 404

    db.execute("UPDATE users SET last_seen = ? WHERE id = ?", (now, user_id))
    db.commit()

    return '', 204


# migrations
def run_migrations(db_path='calefamily.db'):
    import os
    print(">>> Opening database at:", os.path.abspath(db_path))

    conn = sqlite3.connect(db_path)
    cur  = conn.cursor()

    # figure out which columns already exist in users
    cur.execute("PRAGMA table_info(users);")
    existing_users = {row[1] for row in cur.fetchall()}

    if 'first' not in existing_users:
        cur.execute("ALTER TABLE users ADD COLUMN first TEXT NOT NULL DEFAULT '';")
    if 'last' not in existing_users:
        cur.execute("ALTER TABLE users ADD COLUMN last TEXT NOT NULL DEFAULT '';")
    if 'is_approved' not in existing_users:
        cur.execute("ALTER TABLE users ADD COLUMN is_approved INTEGER NOT NULL DEFAULT 0;")
    if 'is_admin' not in existing_users:
        cur.execute("ALTER TABLE users ADD COLUMN is_admin INTEGER NOT NULL DEFAULT 0;")
    if 'last_seen' not in existing_users:
        cur.execute("ALTER TABLE users ADD COLUMN last_seen TEXT;")
    #print("Columns in users table:", existing_users)
    #print(">>> Using DB at:", os.path.abspath('calefamily.db'))

    # notifications table
    cur.execute("""
      CREATE TABLE IF NOT EXISTS notifications (
        id          INTEGER PRIMARY KEY AUTOINCREMENT,
        recipient   INTEGER NOT NULL,
        type        TEXT    NOT NULL,
        payload     TEXT,
        is_read     INTEGER NOT NULL DEFAULT 0,
        created_at  DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY(recipient) REFERENCES users(id)
      );
    """)

    # create messages table
    cur.execute("""
    CREATE TABLE IF NOT EXISTS messages (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        sender_id INTEGER NOT NULL,
        recipient_id INTEGER NOT NULL,
        content TEXT NOT NULL,
        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
        is_read INTEGER NOT NULL DEFAULT 0,
        FOREIGN KEY(sender_id) REFERENCES users(id),
        FOREIGN KEY(recipient_id) REFERENCES users(id)
    );
    """)
    
    # Now migrate messages table
    cur.execute("PRAGMA table_info(messages);")
    existing_msgs = {row[1] for row in cur.fetchall()}

    if 'is_read' not in existing_msgs:
        cur.execute("ALTER TABLE messages ADD COLUMN is_read INTEGER NOT NULL DEFAULT 0;")
    if 'deleted' not in existing_msgs:
        cur.execute("ALTER TABLE messages ADD COLUMN deleted INTEGER NOT NULL DEFAULT 0;")
    if 'message_type' not in existing_msgs:
        cur.execute("ALTER TABLE messages ADD COLUMN message_type TEXT NOT NULL DEFAULT 'mail';")

    conn.commit()
    conn.close()

# … after you configure your Flask `app` and before `app.run()`:
if __name__ == '__main__':
    # ensure new columns & tables exist without touching old data
    init_db()
    run_migrations()
    app.run(host='0.0.0.0', port=5001, debug=True)
