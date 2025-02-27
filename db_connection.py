from config import Config  # Add this import

class Db:
    def __init__(self):
        self.connection = None
        self.cursor = None
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
        except mysql.connector.Error as err:
            print(f"Database connection failed: {err}")
            print(f"Used credentials: {Config.DB_USER}@{Config.DB_HOST}")  # Changed to use Config
            raise