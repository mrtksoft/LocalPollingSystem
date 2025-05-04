# shared/database.py
#Implementation for common database using SQLITE3
## For next version distributed PostgresSQL could be used.

import sqlite3
import os
import threading ## https://docs.python.org/3/library/threading.html



db_path_env = os.getenv('POLLING_DB_PATH')
if not db_path_env:
    raise EnvironmentError("POLLING_DB_PATH environment variable is not set.")

DATABASE_FILE = db_path_env
# Use a threading in local storage for connections to ensure thread safety with SQLite
local_storage = threading.local()

def get_db():
    ## Get SQLite connection for current thread
    if not hasattr(local_storage, 'connection'):
        local_storage.connection = sqlite3.connect(DATABASE_FILE, check_same_thread=False)
        # Return rows as uples and dictionaries // access by index or name
        local_storage.connection.row_factory = sqlite3.Row
    return local_storage.connection

def close_connection(exception=None):
    ## connection closure after rquest
    if hasattr(local_storage, 'connection'):
        local_storage.connection.close()

        delattr(local_storage, 'connection') # Delete attribute // new one is created next time 

def init_db():
    #database schema is initialiezed
    if os.path.exists(DATABASE_FILE):
        print("Database already exists.")
    
    
    print("Initializing database...")
    conn = None
    try:
        # before connecting ensure the file exists
        open(DATABASE_FILE, 'a').close() 
        
        # Connect explicitly for initialization
        conn = sqlite3.connect(DATABASE_FILE)
        cursor = conn.cursor()

        # Polls Table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS polls (
            id TEXT PRIMARY KEY,
            question TEXT NOT NULL,
            options TEXT NOT NULL -- Store options as JSON string
        )
        ''')

        # Votes Table
        ## stores counts per option per poll
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS votes (
            poll_id TEXT NOT NULL,
            option_text TEXT NOT NULL,
            count INTEGER NOT NULL DEFAULT 0,
            PRIMARY KEY (poll_id, option_text),
            FOREIGN KEY (poll_id) REFERENCES polls(id)
        )
        ''')
        
        #Table for duplicate vote tracking
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS voters (
            poll_id TEXT NOT NULL,
            voter_id TEXT NOT NULL, -- e.g., IP Address for simplicity
            voted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY (poll_id, voter_id) 
        )
        ''')


        conn.commit()
        print("Database initialized successfully.")
    except sqlite3.Error as e:

        print(f"Database initialization error: {e}")
    finally:
        if conn:
            conn.close()

if __name__ == '__main__':
    #initialize the DATABASE
    init_db()
