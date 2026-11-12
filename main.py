from fastapi import FastAPI, Depends, HTTPException
import models
from models import Todos, Users
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field
from typing import Annotated, Optional
from database import SessionLocal, engine
from fastapi.responses import JSONResponse
from router import auth, admin
from router.auth import get_current_user

app = FastAPI()


models.Base.metadata.create_all(bind=engine)
app.include_router(auth.router)
app.include_router(admin.router)

class TodoCreate(BaseModel):
    id: int
    title: str
    description: str = Field(max_length=100)
    priority: int = Field(ge=1, le=5)
    completed: bool

class TodoUpdate(BaseModel):
    title: Optional[str] = Field(default=None)
    description: Optional[str] = Field(default=None, max_length=100)
    priority: Optional[int] = Field(default=None, ge=1, le=5)
    completed: Optional[bool] = Field(default=None)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

db_dependency = Annotated[Session, Depends(get_db)]
user_dependency = Annotated[dict, Depends(get_current_user)]

@app.get("/")
def read_todos(db : db_dependency, user: user_dependency):
    if user is None:
        raise HTTPException(status_code=401, detail="User not authenticated")
    
    todos = db.query(Todos).filter(Todos.owner_id == user.get("id")).all()
    return todos

@app.get("/todos/{todo_id}")
def read_specific_todo(todo_id: int, db : db_dependency, user: user_dependency):
    if user is None:
        raise HTTPException(status_code=401, detail="User not authenticated")

    todo = db.query(Todos).filter(Todos.owner_id == user.get("id")).filter(Todos.id == todo_id).first()

    if todo:
        return todo
    
    raise HTTPException(status_code=404, detail="Todo not found")

@app.post("/create/")
def create_todo(new_todo: TodoCreate, db : db_dependency, user: user_dependency):

    if user is None:
        raise HTTPException(status_code=401, detail="User not authenticated")

    todo_model = Todos(**new_todo.model_dump(), owner_id=user.get("id"))  # Set the owner_id to the current user's ID
    db.add(todo_model)
    db.commit() 

    return JSONResponse(content={"message": "Todo created successfully"}, status_code=201)

@app.put("/update/{todo_id}")
def update_todo(todo_id: int, updated_todo: TodoUpdate, db : db_dependency, user: user_dependency):
    if user is None:
        raise HTTPException(status_code=401, detail="User not authenticated")

    todo = db.query(Todos).filter(Todos.owner_id == user.get("id")).filter(Todos.id == todo_id).first()

    if not todo:
        raise HTTPException(status_code=404, detail="Todo not found")

    updated_data = updated_todo.model_dump(exclude_unset=True)

    for key, value in updated_data.items():
        setattr(todo, key, value)

    db.commit()
    return JSONResponse(content={"message": "Todo updated successfully"}, status_code=200)

@app.delete("/delete/{todo_id}")
def delete_todo(todo_id: int, db : db_dependency, user: user_dependency):
    if user is None:
        raise HTTPException(status_code=401, detail="User not authenticated")

    todo = db.query(Todos).filter(Todos.owner_id == user.get("id")).filter(Todos.id == todo_id).first()

    if not todo:
        raise HTTPException(status_code=404, detail="Todo not found")

    db.delete(todo)
    db.commit()
    return JSONResponse(content={"message": "Todo deleted successfully"}, status_code=200)

@app.get("/userprofile")
def get_user_profile(user: user_dependency, db : db_dependency):
    if user is None:
        raise HTTPException(status_code=401, detail="User not authenticated")
    
    user_profile = db.query(Users).filter(Users.id == user.get("id")).first()
    return user_profile

@app.put("/updateprofile")
def update_user_profile(updated_user: auth.UpdateUser, db : db_dependency, user: user_dependency):
    if user is None:
        raise HTTPException(status_code=401, detail="User not authenticated")

    user_model = db.query(Users).filter(Users.id == user.get("id")).first()

    updated_data = updated_user.model_dump(exclude_unset=True)

    for key, value in updated_data.items():
        setattr(user_model, key, value)

    db.commit()
    return JSONResponse(content={"message": "User profile updated successfully"}, status_code=200)