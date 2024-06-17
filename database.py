# database.py

import sqlite3

def setup_database():
    conn = sqlite3.connect('timing_data.db')
    c = conn.cursor()

    # Create athletes table if it doesn't exist
    c.execute('''CREATE TABLE IF NOT EXISTS athletes (
                    id INTEGER PRIMARY KEY,
                    name TEXT NOT NULL UNIQUE
                )''')

    # Insert initial athlete names if the table is empty
    c.execute("SELECT COUNT(*) FROM athletes")
    count = c.fetchone()[0]
    if count == 0:
        initial_athletes = ['Test Athlete']
        for athlete in initial_athletes:
            c.execute("INSERT INTO athletes (name) VALUES (?)", (athlete,))
            print(f"Inserted athlete: {athlete}")

    conn.commit()
    conn.close()

if __name__ == "__main__":
    setup_database()
