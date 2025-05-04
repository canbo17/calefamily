import sqlite3

def update_users_table():
    conn = sqlite3.connect('calefamily.db')
    c = conn.cursor()

    try:
        c.execute("ALTER TABLE users ADD COLUMN profile_pic TEXT;")
    except sqlite3.OperationalError:
        pass
    try:
        c.execute("ALTER TABLE users ADD COLUMN zodiac_sign TEXT;")
    except sqlite3.OperationalError:
        pass
    try:
        c.execute("ALTER TABLE users ADD COLUMN birth_year INTEGER;")
    except sqlite3.OperationalError:
        pass
    try:
        c.execute("ALTER TABLE users ADD COLUMN favorite_color TEXT;")
    except sqlite3.OperationalError:
        pass
    try:
        c.execute("ALTER TABLE users ADD COLUMN favorite_animal TEXT;")
    except sqlite3.OperationalError:
        pass
    try:
        c.execute("ALTER TABLE users ADD COLUMN favorite_subject TEXT;")
    except sqlite3.OperationalError:
        pass
    try:
        c.execute("ALTER TABLE users ADD COLUMN favorite_hobby TEXT;")
    except sqlite3.OperationalError:
        pass
    try:
        c.execute("ALTER TABLE users ADD COLUMN favorite_movie TEXT;")
    except sqlite3.OperationalError:
        pass
    try:
        c.execute("ALTER TABLE users ADD COLUMN favorite_book TEXT;")
    except sqlite3.OperationalError:
        pass

    c.execute('''
    CREATE TABLE IF NOT EXISTS messages (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        sender_id INTEGER,
        recipient_id INTEGER,
        content TEXT,
        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY(sender_id) REFERENCES users(id),
        FOREIGN KEY(recipient_id) REFERENCES users(id)
    )
    ''')

    c.execute('''
    CREATE TABLE IF NOT EXISTS reactions (
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

    conn.commit()
    conn.close()

def add_is_read_column():
    conn = sqlite3.connect('calefamily.db')
    c = conn.cursor()

    # Add 'is_read' column to the 'messages' table
    c.execute('ALTER TABLE messages ADD COLUMN is_read INTEGER DEFAULT 0')

    conn.commit()
    conn.close()

if __name__ == "__main__":
    update_users_table()
    add_is_read_column()
    print("Database updated successfully!")