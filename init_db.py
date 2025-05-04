import sqlite3

# Connect to the database
conn = sqlite3.connect('calefamily.db')
c = conn.cursor()  # Define the cursor 'c' to interact with the database

# Create users table (if not exists)
c.execute('''
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT NOT NULL UNIQUE,
    password TEXT NOT NULL
)
''')

# Create posts table (if not exists)
c.execute('''
CREATE TABLE IF NOT EXISTS posts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    subcale_name TEXT,
    content TEXT NOT NULL,
    hearts INTEGER DEFAULT 0,
    laughs INTEGER DEFAULT 0,
    notes INTEGER DEFAULT 0,
    thumbs INTEGER DEFAULT 0,
    FOREIGN KEY(user_id) REFERENCES users(id)
)
''')

# Create comments table (if not exists)
c.execute('''
CREATE TABLE IF NOT EXISTS comments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    post_id INTEGER,
    user_id INTEGER,
    comment TEXT NOT NULL,
    parent_comment_id INTEGER,
    hearts INTEGER DEFAULT 0,    -- Added hearts column
    laughs INTEGER DEFAULT 0,    -- Added laughs column
    notes INTEGER DEFAULT 0,     -- Added notes column
    thumbs INTEGER DEFAULT 0,    -- Added thumbs column
    FOREIGN KEY(post_id) REFERENCES posts(id),
    FOREIGN KEY(user_id) REFERENCES users(id),
    FOREIGN KEY(parent_comment_id) REFERENCES comments(id)
)
''')

# Create reactions table for both posts and comments
c.execute('''
CREATE TABLE IF NOT EXISTS reactions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    post_id INTEGER,
    comment_id INTEGER,  -- added this line for comment reactions
    user_id INTEGER,
    reaction TEXT,
    FOREIGN KEY(post_id) REFERENCES posts(id),
    FOREIGN KEY(comment_id) REFERENCES comments(id),  -- link to comment
    FOREIGN KEY(user_id) REFERENCES users(id)
)
''')


# Commit the changes and close the connection
conn.commit()
conn.close()

print("Database initialized successfully!")