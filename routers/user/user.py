# FastAPI
from fastapi import APIRouter, Depends, HTTPException, Request, Header
from sqlalchemy.orm import Session
from typing import List

import schemas, database
from routers.user import crud

router = APIRouter(
    prefix="/users",
    tags=["user"],
    responses={404: {"description": "Not found"}}
)

# Dependency
def get_db():
    db = database.SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.post("/", response_model=schemas.User)
def create_user(user: schemas.UserCreate, db: Session = Depends(get_db)):
    db_user = crud.get_user_by_line_id(db, line_id=user.line_id)
    if db_user:
        raise HTTPException(status_code=400, detail="Line ID already registered")
    return crud.create_user(db=db, user=user)

@router.get("/", response_model=List[schemas.User])
def read_users(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return crud.get_users(db, skip=skip, limit=limit)

@router.get("/{user_id}", response_model=schemas.User)
def read_user(user_id: int, db: Session = Depends(get_db)):
    db_user = crud.get_user(db, user_id=user_id)
    if db_user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return db_user

@router.get("/line_id/{line_id}", response_model=schemas.User)
def read_user_by_line_id(line_id: str, db: Session = Depends(get_db)):
    db_user = crud.get_user_by_line_id(db, line_id=line_id)
    if db_user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return db_user

# User State
@router.get("/state/lineid/{line_id}", response_model=schemas.UserState)
def read_user_state_by_line_id(line_id: str, db: Session = Depends(get_db)):
    db_user_state = crud.get_user_state_by_line_id(db, line_id=line_id)
    if db_user_state is None:
        raise HTTPException(status_code=404, detail="User not found")
    return db_user_state

