from sqlite3 import connect

con = connect('patterns.sqlite')
cur = con.cursor()
with open('create_my_db.sql', 'r') as f:
    text = f.read()
cur.executescript(text)
cur.close()
con.close()