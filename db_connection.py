import mysql.connector
from contextlib import contextmanager
from config import Config

class Db:
    def __init__(self):
        self.connection = None
        self.cursor = None
        
    def __enter__(self):
        try:
            self.connection = mysql.connector.connect(
                host=Config.DB_HOST,
                user=Config.DB_USER,
                password=Config.DB_PASSWORD,
                database=Config.DB_NAME,
                port=Config.DB_PORT,
                auth_plugin='mysql_native_password'
            )
            self.cursor = self.connection.cursor(dictionary=True)
            return self
        except mysql.connector.Error as err:
            print(f"Database connection failed: {err}")
            raise

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.cursor:
            self.cursor.close()
        if self.connection:
            self.connection.close()

    def execute(self, query, params=None):
        try:
            self.cursor.execute(query, params or ())
            self._clear_unread_results()  # Clear unread results before committing
            self.connection.commit()
            return self.cursor.rowcount
        except mysql.connector.Error as err:
            self.connection.rollback()
            raise

    def query(self, query, params=None):
        self.cursor.execute(query, params or ())
        return self

    def fetchone(self):
        if self.cursor.with_rows:  # Check if there is a result set
            return self.cursor.fetchone()
        return None

    def fetchall(self):
        if self.cursor.with_rows:  # Check if there is a result set
            return self.cursor.fetchall()
        return []

    def _clear_unread_results(self):
        """Clear any unread results from the cursor."""
        while self.cursor.nextset():
            pass