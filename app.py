from flask import Flask, render_template, request, redirect, session, url_for
import sqlite3
import os

app = Flask(__name__)
app.secret_key = 'your_secret_key'

DB_FILE = 'calefamily.db'

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

# Home page
@app.route('/')
def home():
    subcales = [
        {'name': 'Caleducation', 'emoji': '📚'},
        {'name': 'Calecho', 'emoji': '🎵'},
        {'name': 'Calentertainment', 'emoji': '🎬'},
        {'name': 'Calexplore', 'emoji': '🌎'},
        {'name': 'Calenrichment', 'emoji': '🎨'},
        {'name': 'Calespañol', 'emoji': '🗣️'}
    ]
    return render_template('home.html', subcales=subcales)

# Register
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        confirm = request.form['confirm']

        if password != confirm:
            return "Passwords do not match."

        conn = sqlite3.connect(DB_FILE)
        c = conn.cursor()
        try:
            c.execute('INSERT INTO users (username, password) VALUES (?, ?)', (username, password))
            conn.commit()
        except sqlite3.IntegrityError:
            return "Username already exists."
        finally:
            conn.close()

        return redirect('/login')
    return render_template('register.html')

# Login
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        conn = sqlite3.connect(DB_FILE)
        c = conn.cursor()
        c.execute('SELECT id FROM users WHERE username = ? AND password = ?', (username, password))
        user = c.fetchone()
        conn.close()

        if user:
            session['user_id'] = user[0]
            session['username'] = username
            return redirect('/')
        else:
            return "Invalid login."
    return render_template('login.html')

# Logout
@app.route('/logout')
def logout():
    session.clear()
    return redirect('/')

# Subcale page
@app.route('/subcale/<subcale_name>', methods=['GET', 'POST'])
def subcale(subcale_name):
    if 'user_id' not in session:
        return redirect('/login')

    conn = sqlite3.connect('calefamily.db')
    c = conn.cursor()

    if request.method == 'POST':
        content = request.form['content']
        c.execute('INSERT INTO posts (user_id, subcale_name, content) VALUES (?, ?, ?)',
                  (session['user_id'], subcale_name, content))
        conn.commit()

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
    return render_template('subcale.html', subcale_name=subcale_name, posts=posts_with_comments)

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

# Profiles
@app.route('/profile')
def profile():
    if 'user_id' not in session:
        return redirect('/login')
    
    conn = sqlite3.connect('calefamily.db')
    c = conn.cursor()
    c.execute('SELECT username, profile_pic, zodiac_sign, birth_year, favorite_color, favorite_animal, favorite_subject, favorite_hobby, favorite_movie, favorite_book FROM users WHERE id = ?', (session['user_id'],))
    user = c.fetchone()

    # Get unread message count
    c.execute('''
        SELECT COUNT(*) FROM messages
        WHERE recipient_id = ? AND is_read = 0
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
        SELECT username, profile_pic, zodiac_sign, birth_year, favorite_color, 
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

def view_user_profile(user_id):
    if 'user_id' not in session:
        return redirect('/login')

    conn = sqlite3.connect('calefamily.db')
    c = conn.cursor()
    c.execute('SELECT username, profile_pic, zodiac_sign, birth_year, favorite_color, favorite_animal, favorite_subject, favorite_hobby, favorite_movie, favorite_book FROM users WHERE id = ?', (user_id,))
    user = c.fetchone()
    conn.close()

    return render_template('user_profile.html', user=user)

@app.route('/send_messages/<recipient_id>', methods=['GET', 'POST'])
def send_messages(recipient_id):
    if 'user_id' not in session:
        return redirect('/login')

    # Handle message composition (POST request)
    if request.method == 'POST':
        content = request.form['message_content']

        # Save message to database
        conn = sqlite3.connect('calefamily.db')
        c = conn.cursor()
        c.execute('INSERT INTO messages (sender_id, recipient_id, content) VALUES (?, ?, ?)', 
                  (session['user_id'], recipient_id, content))
        
        # Optional: add a "read" flag for future use (for inbox management)
        conn.commit()
        conn.close()

        # Redirect user back to inbox after sending message
        return redirect('/inbox')

    # If GET request, show the message form
    conn = sqlite3.connect('calefamily.db')
    c = conn.cursor()
    c.execute('SELECT username FROM users WHERE id = ?', (recipient_id,))
    recipient = c.fetchone()
    conn.close()

    if not recipient:
        return "User not found."

    # Pass recipient id to the template for message composition
    return render_template('send_messages.html', recipient=recipient[0], recipient_id=recipient_id)

@app.route('/inbox')
def inbox():
    if 'user_id' not in session:
        return redirect('/login')

    conn = sqlite3.connect('calefamily.db')
    c = conn.cursor()
    c.execute('''
        SELECT users.username, messages.content, messages.timestamp, messages.is_read
        FROM messages
        JOIN users ON messages.sender_id = users.id
        WHERE messages.recipient_id = ? AND messages.is_read = 0
        ORDER BY messages.timestamp DESC
    ''', (session['user_id'],))
    unread_messages = c.fetchall()
    conn.close()

    return render_template('inbox.html', messages=unread_messages)

@app.route('/deleted_messages')
def deleted_messages():
    if 'user_id' not in session:
        return redirect('/login')

    conn = sqlite3.connect('calefamily.db')
    c = conn.cursor()
    c.execute('''
        SELECT users.username, messages.content, messages.timestamp
        FROM messages
        JOIN users ON messages.sender_id = users.id
        WHERE messages.recipient_id = ? AND messages.deleted = 1
        ORDER BY messages.timestamp DESC
    ''', (session['user_id'],))
    messages = c.fetchall()
    conn.close()

    return render_template('deleted_messages.html', messages=messages)

@app.route('/mark_as_read/<int:message_id>')
def mark_as_read(message_id):
    if 'user_id' not in session:
        return redirect('/login')

    conn = sqlite3.connect('calefamily.db')
    c = conn.cursor()
    c.execute('UPDATE messages SET is_read = 1 WHERE id = ? AND recipient_id = ?', (message_id, session['user_id']))
    conn.commit()
    conn.close()

    return redirect('/inbox')

def add_message_flags():
    conn = sqlite3.connect('calefamily.db')
    c = conn.cursor()
    
    # Check if 'read' column exists
    c.execute("PRAGMA table_info(messages)")
    columns = [column[1] for column in c.fetchall()]
    
    if 'read' not in columns:
        c.execute('ALTER TABLE messages ADD COLUMN read INTEGER DEFAULT 0')  # 0 for unread, 1 for read
    
    if 'deleted' not in columns:
        c.execute('ALTER TABLE messages ADD COLUMN deleted INTEGER DEFAULT 0')  # 0 for not deleted, 1 for deleted
    
    conn.commit()
    conn.close()

if __name__ == '__main__':
    init_db()
    app.run(debug=True, host="0.0.0.0", port=5001)