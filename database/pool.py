# NOTE: ONLY IMPORT THIS FILE FROM database/database.py !!!
# NOTE: otherwise pool will be created multiple times
import os

from dotenv import load_dotenv
from psycopg2.pool import ThreadedConnectionPool
from psycopg2.extensions import cursor as Cursor


load_dotenv()

USER = os.getenv("USERDB")  # gatterle
PASSWORD = os.getenv("PASSWORD")
HOST = os.getenv("HOST")  # localhost
PORT = os.getenv("PORT")  # 5432
DBNAME = os.getenv("DBNAME")  # mhbs


def create_pool(max_connections: int = 100, min_connections: int = 20):
    """
    create_pool \n
    creates a thread pool safely

    Args:
    max_connections (int): maximum number of connections
    min_connections (int): minimum number of connections
    Returns:
        connection_pool:connection_pool
    """
    connection_pool = ThreadedConnectionPool(
        minconn=min_connections,
        maxconn=max_connections,
        user=USER,
        password=PASSWORD,
        host=HOST,
        port=PORT,
        database=DBNAME,
    )

    if not connection_pool:
        raise Exception("Creation of connection pool failed")
    return connection_pool


def get_cursor() -> Cursor:
    """
    get a cursor from the pool

    Returns:
        Cursor: cursor object for database
    """
    return pool.getconn().cursor()


def close_cursor(cursor: Cursor) -> None:
    """
    close a cursor and return the connection to the pool

    Args:
        Cursor: cursor object to close
    """
    cursor.close()
    pool.putconn(cursor.connection)


# TODO: move this to database/database.py maybe
# create pool
pool: ThreadedConnectionPool = create_pool()
