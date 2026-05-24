from src.db.models.user import User


def create_user():
    return User(name="demo")

