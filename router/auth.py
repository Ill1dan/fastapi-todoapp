from fastapi import FastAPI, HTTPException, APIRouter, Depends
from sqlalchemy.orm import Session
from fastapi.responses import JSONResponse
from typing import Annotated, Optional, cast
from pydantic import BaseModel, Field
from database import SessionLocal
from models import Users
from passlib.context import CryptContext
from fastapi.security import OAuth2PasswordRequestForm, OAuth2PasswordBearer
from jose import jwt
from datetime import timedelta, datetime, timezone

router = APIRouter()

bcrypt_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
OAuth2_bearer = OAuth2PasswordBearer(tokenUrl="login/")

SECRET_KEY = "b712ef4e158aa1de0d4de63a2bfbf5a180987a2e8fdb1d260e6fdb8df4038c8c"
ALGORITHM = "HS256"

class UserCreate(BaseModel):
    username: str
    email: str
    firstname: str
    lastname: str
    password: str
    role: str
    phone_number: str

class UpdateUser(BaseModel):
    username: Optional[str] = Field(default=None, max_length=50)
    email: Optional[str] = Field(default=None)
    firstname: Optional[str] = Field(default=None)
    lastname: Optional[str] = Field(default=None)
    phone_number: Optional[str] = Field(default=None, max_length=11)

class PasswordChange(BaseModel):
    old_password: str
    new_password: str

def authenticate_user(db: Session, username: str, password: str):
    user = db.query(Users).filter(Users.username == username).first()

    if not user:
        return None
    if not bcrypt_context.verify(password, user.hash_password):
        return None
    
    return user

def create_access_token(username: str, user_id: int, user_role: str, expires_delta: timedelta):
    encode = {"sub": username, "id": user_id, "role": user_role}
    expire = datetime.now(timezone.utc) + expires_delta
    encode.update({"exp": expire})
    return jwt.encode(encode, SECRET_KEY, algorithm=ALGORITHM)

def get_current_user(token: Annotated[str, Depends(OAuth2_bearer)]):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = cast(str, payload.get("sub"))
        user_id: int = cast(int, payload.get("id"))
        user_role: str = cast(str, payload.get("role"))

        if username is None or user_id is None:
            raise HTTPException(status_code=401, detail="User not found")
        
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid token")

    return {"username": username, "id": user_id, "role": user_role}
    

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

db_dependency = Annotated[Session, Depends(get_db)]
user_dependency = Annotated[dict, Depends(get_current_user)]

@router.post("/createuser/")
def create_user(new_user: UserCreate, db : db_dependency):

    user_model = Users(
        username=new_user.username,
        email=new_user.email,
        firstname=new_user.firstname,
        lastname=new_user.lastname,
        hash_password=bcrypt_context.hash(new_user.password),
        is_active=True,
        role=new_user.role,
        phone_number=new_user.phone_number
    )

    db.add(user_model)
    db.commit() 

    return JSONResponse(content={"message": "User created successfully"}, status_code=201)

@router.post("/login/")
def login_user(form_data: Annotated[OAuth2PasswordRequestForm, Depends()], db : db_dependency):

    user = authenticate_user(db, form_data.username, form_data.password)

    if user is None:
        return JSONResponse(content={"message": "Invalid credentials"}, status_code=401)
    
    token = create_access_token(cast(str, user.username), cast(int, user.id), cast(str, user.role), timedelta(minutes=30))

    return JSONResponse(content={"access_token": token, "token_type": "bearer"}, status_code=200)

@router.put("/passwordchange/")
def update_password(user : user_dependency, password_change: PasswordChange, db : db_dependency):

    if user is None:
        raise HTTPException(status_code=401, detail="User not authenticated")

    user_model = db.query(Users).filter(Users.id == user.get("id")).first()

    if user_model is None:
        raise HTTPException(status_code=404, detail="User not found")

    if not bcrypt_context.verify(password_change.old_password, user_model.hash_password):
        raise HTTPException(status_code=401, detail="Old password is incorrect")

    user_model.hash_password = bcrypt_context.hash(password_change.new_password)

    db.add(user_model)
    db.commit()
    return JSONResponse(content={"message": "Password updated successfully"}, status_code=200)