import sqlite3

from config import DATABASE_PATH


class Database:

    def __init__(self):

        DATABASE_PATH.parent.mkdir(parents=True, exist_ok=True)

        self.connection = sqlite3.connect(DATABASE_PATH)
        self.cursor = self.connection.cursor()

        self.create_tables()

    def create_tables(self):

        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (

                id INTEGER PRIMARY KEY AUTOINCREMENT,

                username TEXT UNIQUE NOT NULL,

                full_name TEXT NOT NULL,

                model_path TEXT,

                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP

            )
        """)

        self.connection.commit()
    def user_exists(self, username):

        self.cursor.execute("""
            SELECT 1
            FROM users
            WHERE username = ?
        """, (username,))

        return self.cursor.fetchone() is not None

    def register_user(self, username, full_name):
        if self.user_exists(username):
            raise ValueError("Username already exists.")
        self.cursor.execute("""
            INSERT INTO users(username, full_name)
            VALUES(?, ?)
        """, (username, full_name))

        self.connection.commit()

    def update_model(self, username, model_path):

        self.cursor.execute("""
            UPDATE users
            SET model_path = ?
            WHERE username = ?
        """, (model_path, username))

        self.connection.commit()

    def get_user(self, username):

        self.cursor.execute("""
            SELECT *
            FROM users
            WHERE username = ?
        """, (username,))

        return self.cursor.fetchone()

    def get_all_users(self):

        self.cursor.execute("""
            SELECT *
            FROM users
        """)

        return self.cursor.fetchall()

    def delete_user(self, username):

        self.cursor.execute("""
            DELETE FROM users
            WHERE username = ?
        """, (username,))

        self.connection.commit()

    def close(self):

        self.connection.close()


if __name__ == "__main__":

    db = Database()

    db.register_user(
        "abhijeet",
        "Abhijeet Warudkar"
    )

    print(db.get_user("abhijeet"))

    print()

    print(db.get_all_users())

    db.close()