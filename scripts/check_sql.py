import sqlite3

# Connect to the database (it will create the database if it doesn't exist)
conn = sqlite3.connect('calefamily.db')

# Create a cursor object
c = conn.cursor()

# Show all tables in the database
c.execute("SELECT name FROM sqlite_master WHERE type='table';")
tables = c.fetchall()
print(tables)

# Check the structure of the 'posts' table
c.execute("PRAGMA table_info(posts);")
columns = c.fetchall()
print(columns)

# Close the connection
conn.close()
