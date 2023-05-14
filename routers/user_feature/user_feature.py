from fastapi import APIRouter, Depends, HTTPException, Request, Header
from sqlalchemy.orm import Session
from typing import List, Dict

import schemas, database
from routers.user_feature import crud

router = APIRouter(
    prefix="/user_features",
    tags=["user_feature"],
    responses={404: {"description": "Not found"}}
)

# Dependency
def get_db():
    db = database.SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post("/", response_model=schemas.UserFeature)
def create_user_feature(user_feature: schemas.UserFeatureCreate, db: Session = Depends(get_db)):
    return crud.create_user_feature(db=db, user_feature=user_feature)

@router.get("/", response_model=List[schemas.UserFeature])
def read_user_features(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return crud.get_user_features(db, skip=skip, limit=limit)

@router.get("/userid/{user_id}", response_model=List[schemas.UserFeature])
def read_user_feature_by_user_id(user_id: int, db: Session = Depends(get_db)):
    db_user_feature = crud.get_user_feature_by_user_id(db, user_id=user_id)
    if db_user_feature is None:
        raise HTTPException(status_code=404, detail="UserFeature not found")
    return db_user_feature

@router.get("/lineid/{line_id}", response_model=List[schemas.UserFeature])
def read_user_feature_by_line_user_id(line_id: str, db: Session = Depends(get_db)):
    db_user_feature = crud.get_user_feature_by_line_id(db, line_id=line_id)
    if db_user_feature is None:
        raise HTTPException(status_code=404, detail="UserFeature not found")
    return db_user_feature