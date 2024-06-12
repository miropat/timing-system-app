import sqlite3


def setup_database():
    conn = sqlite3.connect('timing_data.db')
    c = conn.cursor()

    c.execute('''
    CREATE TABLE IF NOT EXISTS timings (
        id INTEGER PRIMARY KEY,
        duration INTEGER,
        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
    )
    ''')

    conn.commit()
    conn.close()