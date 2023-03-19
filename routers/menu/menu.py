from fastapi import APIRouter, Depends, HTTPException, Request, Header
from sqlalchemy.orm import Session
from typing import List, Dict

import schemas, database
from routers.menu import crud

router = APIRouter(
    prefix="/menus",
    tags=["menu"],
    responses={404: {"description": "Not found"}}
)

# Dependency
def get_db():
    db = database.SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.post("/", response_model=schemas.Menu)
def create_menu(menu: schemas.MenuCreate, db: Session = Depends(get_db)):
    db_menu = crud.get_menu_by_name(db, name=menu.name)
    if db_menu:
        raise HTTPException(status_code=400, detail="Menu already registered")
    return crud.create_menu(db=db, menu=menu)

@router.get("/", response_model=Dict[str, schemas.Menu])
def read_menus(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return crud.get_menus(db, skip=skip, limit=limit)

@router.get("/{menu_id}", response_model=schemas.Menu)
def read_menu(menu_id: int, db: Session = Depends(get_db)):
    db_menu = crud.get_menu(db, menu_id=menu_id)
    if db_menu is None:
        raise HTTPException(status_code=404, detail="Menu not found")
    return db_menu