import logging
from retry import retry
import sqlite3
from sqlite3 import OperationalError, Error, Connection

import config

MAX_WRITE_ATTEMPTS=5

def create_connection(db_file):
    """ create a database connection to a SQLite database """
    conn = None
    try:
        conn = sqlite3.connect(db_file)
        print(sqlite3.version)
    except Error as e:
        print(e)
    finally:
        if conn:
            conn.close()

def create_tables():
    query = """
    CREATE TABLE IF NOT EXISTS artists (
    id TEXT PRIMARY KEY,
    name TEXT,
    genres TEXT,
    popularity INTEGER
    )
    """

    conn = sqlite3.connect(config.DB_FILE)

    try:
        cur = conn.cursor()
        cur.execute(query)

        conn.commit()
    except Error as e:
        logging.error(f'unable to create artists table: {e}')
        


# kind of hacky but lets just retry if we get operational error
@retry(OperationalError, delay=0.5, tries=MAX_WRITE_ATTEMPTS)
def save_artists(*artists):
    save_artist_query = """
    INSERT OR IGNORE INTO artists VALUES (?,?,?,?);
    """

    # create connection here since this will be called from seperate
    # threads and processes
    conn = sqlite3.connect(config.DB_FILE)

    try:
        cur = conn.cursor()
        cur.executemany(save_artist_query, artists)

        conn.commit()
    except OperationalError as e:
        # may be raised since we are using multiple processes
        logging.error(f'error saving artists to db: {e}')
        raise

