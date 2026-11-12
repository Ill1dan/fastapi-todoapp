from fastapi import FastAPI, HTTPException, APIRouter, Depends
from sqlalchemy.orm import Session
from fastapi.responses import JSONResponse
from typing import Annotated, Optional, cast
from pydantic import BaseModel
from database import SessionLocal
from models import Users
from passlib.context import CryptContext
from fastapi.security import OAuth2PasswordRequestForm, OAuth2PasswordBearer
from jose import jwt
from datetime import timedelta, datetime, timezone
from router.auth import get_current_user
from models import Todos

router = APIRouter()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

db_dependency = Annotated[Session, Depends(get_db)]
user_dependency = Annotated[dict, Depends(get_current_user)]

@router.get("/admin/todos")
def read_all(db : db_dependency, user: user_dependency):
    if user is None or user.get("role") != "admin":
        raise HTTPException(status_code=401, detail="User not authenticated")
    
    todos = db.query(Todos).all()
    return todos

@router.delete("/admin/delete/{todo_id}")
def delete_todo(todo_id: int, db : db_dependency, user: user_dependency):
    if user is None or user.get("role") != "admin":
        raise HTTPException(status_code=401, detail="User not authenticated")

    todo = db.query(Todos).filter(Todos.id == todo_id).first()

    if not todo:
        raise HTTPException(status_code=404, detail="Todo not found")

    db.delete(todo)
    db.commit()
    return JSONResponse(content={"message": "Todo deleted successfully"}, status_code=200)