import sqlite3
conn = sqlite3.connect('chatbot_sessions.sqlite')
cur = conn.cursor()
cur.execute("SELECT name FROM sqlite_master WHERE type='table';")
tables = cur.fetchall()
print('Tables:', tables)
for table_name, in tables:
    print(f'\nRows in {table_name}:')
    for row in cur.execute(f'SELECT * FROM {table_name} LIMIT 5;'):
        print(row)
conn.close()