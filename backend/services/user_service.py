from pymongo import MongoClient
from config import MONGO_URI, DB_NAME
from werkzeug.security import generate_password_hash, check_password_hash

class UserService:
    def __init__(self):
        self.client = MongoClient(MONGO_URI)
        self.db = self.client[DB_NAME]
        self.collection = self.db["users"]

    def create_user(self, username, email, password):
        hashed_password = generate_password_hash(password)  # Hacher le mot de passe
        user = {"username": username, "email": email, "password": hashed_password}
        self.collection.insert_one(user)
        return user

    def find_user_by_email(self, email):
        return self.collection.find_one({"email": email})

    def verify_password(self, email, password):
        user = self.find_user_by_email(email)
        if user and check_password_hash(user["password"], password):
            return user
        return None
