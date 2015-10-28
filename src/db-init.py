import sqlite3 as sql
import sys


# Creates /__cache__/ if it doesn't already exist.
if not os.path.exists('./__cache__/'):
    os.makedirs('./__cache__/')

# Initiates connection.
con = sql.connect('./__cache__/living_in_the_.db')

# Prepopulated list for testing.
OPS = ["bo1g", "rekyuu", "Luminarys", "Mei-mei", "nuck", "tsunderella",
       "Liseda", "Wizzie", "Wizbright", "remove_me", "adrl"]

# Uses the connection until everything is done, then closes it.
with con:

    # Allows the use of dictionaries for rows.
    con.row_factory = sql.Row

    # Used for database manipulation.
    db = con.cursor()

    # Drops the table if it exists and creates it if it does not.
    # :Id INTEGER PRIMARY KEY - auto increments Id field (integer)
    # :Name TEXT - the username, a string.
    db.execute('DROP TABLE IF EXISTS Ops;')
    db.execute(
        'CREATE TABLE IF NOT EXISTS Ops(Id INTEGER PRIMARY KEY, Name TEXT);')

    # Loop to populate the table.
    for op in OPS:
        db.execute("INSERT INTO Ops(Name) VALUES('{0}');".format(op))

    # Method to read everything from the table.
    db.execute('SELECT * FROM Ops;')
    rows = db.fetchall()

    # Loop to print the rows to console.
    for row in rows:
        print(row['Name'])

    # Deletion method.
    delete = 'remove_me'
    db.execute("DELETE FROM Ops WHERE Name='{0}';".format(delete))

    db.execute('SELECT * FROM Ops;')
    rows = db.fetchall()

    for row in rows:
        print(row['Name'])
