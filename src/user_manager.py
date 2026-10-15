from pathlib import Path
import shutil

from .config import USER_DATA_DIR
from .database import Database


class UserManager:

    def __init__(self):

        self.database = Database()

    def register_user(self, username, full_name, uploaded_files):

        username = username.strip().lower()

        if not username:
            raise ValueError("Username cannot be empty.")

        if len(uploaded_files) == 0:
            raise ValueError("Please upload at least one signature.")

        if self.database.user_exists(username):
            raise ValueError("Username already exists.")

        user_folder = USER_DATA_DIR / username
        genuine_folder = user_folder / "genuine"

        genuine_folder.mkdir(parents=True, exist_ok=True)

        for index, uploaded_file in enumerate(uploaded_files, start=1):

            extension = Path(uploaded_file.filename).suffix.lower()

            destination = genuine_folder / f"signature_{index}{extension}"

            with open(destination, "wb") as file:
                shutil.copyfileobj(uploaded_file, file)

        self.database.register_user(username, full_name)

        return user_folder

    def get_users(self):

        return self.database.get_all_users()

    def get_user(self, username):

        return self.database.get_user(username)