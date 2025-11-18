import sqlite3

# Connect to your database file
conn = sqlite3.connect("users.db")
c = conn.cursor()

# Fetch all rows from usertbl
c.execute("SELECT id, username, password_hash, secret FROM usertbl")
rows = c.fetchall()

# Print results nicely
print("Users in Database:")
for row in rows:
    print(f"ID: {row[0]}, Username: {row[1]}, Password Hash: {row[2]}, Secret: {row[3]}")

conn.close()
