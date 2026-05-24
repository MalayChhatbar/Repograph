from fastapi import APIRouter

from src.services.user_service import create_user

router = APIRouter()


@router.get("/users")
def list_users():
    return []


@router.post("/users")
def create_user_route():
    return create_user()

