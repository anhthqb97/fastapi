from fastapi import APIRouter

router = APIRouter()

@router.get("/users/", tags=["users"])
async def read_users():
    return [{"username": "John", "email": "jf@gmail.com"}]

@router.get("/users/me", tags=["users"])
async def read_users_me():
    return {"username": "fakeusername", "email": "fake@gmail.com"}

@router.get("/users/{username}", tags=["users"])
async def read_user(username: str):
    return {"username": username, "email": "Fake so easy"}