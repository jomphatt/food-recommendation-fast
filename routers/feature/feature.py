from fastapi import APIRouter, Depends, HTTPException, Request, Header
from sqlalchemy.orm import Session
from typing import List, Dict

import schemas, database
from routers.feature import crud

router = APIRouter(
    prefix="/features",
    tags=["feature"],
    responses={404: {"description": "Not found"}}
)

# Dependency
def get_db():
    db = database.SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post("/", response_model=schemas.Feature)
def create_feature(feature: schemas.FeatureCreate, db: Session = Depends(get_db)):
    db_feature = crud.get_feature_by_name(db, name=feature.name)
    if db_feature:
        raise HTTPException(status_code=400, detail="Feature already registered")
    return crud.create_feature(db=db, feature=feature)

@router.get("/", response_model=List[schemas.Feature])
def read_features(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return crud.get_features(db, skip=skip, limit=limit)

@router.get("/{feature_id}", response_model=schemas.Feature)
def read_feature(feature_id: int, db: Session = Depends(get_db)):
    db_feature = crud.get_feature(db, feature_id=feature_id)
    if db_feature is None:
        raise HTTPException(status_code=404, detail="Feature not found")
    return db_feature