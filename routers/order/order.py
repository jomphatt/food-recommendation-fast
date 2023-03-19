from fastapi import APIRouter, Depends, HTTPException, Request, Header
from sqlalchemy.orm import Session
from typing import List

import schemas, database
from routers.order import crud

router = APIRouter(
    prefix="/orders",
    tags=["order"],
    responses={404: {"description": "Not found"}}
)

# Dependency
def get_db():
    db = database.SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post("/", response_model=schemas.Order)
def create_order(order: schemas.OrderCreate, db: Session = Depends(get_db)):
    return crud.create_order(db=db, order=order)

@router.get("/", response_model=List[schemas.Order])
def read_orders(db: Session = Depends(get_db)):
    return crud.get_orders(db)

@router.get("/{order_id}", response_model=schemas.Order)
def read_order(order_id: int, db: Session = Depends(get_db)):
    db_order = crud.get_order(db, order_id=order_id)
    if db_order is None:
        raise HTTPException(status_code=404, detail="Order not found")
    return db_order

@router.get("/user/{user_id}", response_model=List[schemas.Order])
def read_order_by_user_id(user_id: int, db: Session = Depends(get_db)):
    db_order = crud.get_order_by_user_id(db, user_id=user_id)
    if db_order is None:
        raise HTTPException(status_code=404, detail="Order not found")
    return db_order