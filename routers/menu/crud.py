from sqlalchemy.orm import Session

import models, schemas

# Menu
def get_menu(db: Session, menu_id: int):
    return db.query(models.Menu).filter(models.Menu.id == menu_id).first()

def get_menu_by_name(db: Session, name: str):
    return db.query(models.Menu).filter(models.Menu.name == name).first()

def get_menus(db: Session, skip: int = 0, limit: int = 100):
    all_menus = db.query(models.Menu).offset(skip).limit(limit).all()
    return {x.id: x for x in all_menus}

def create_menu(db: Session, menu: schemas.MenuCreate):
    db_menu = models.Menu(**menu.dict())
    db.add(db_menu)
    db.commit()
    db.refresh(db_menu)
    return db_menu

def get_menus_for_recommendation(db: Session):
    all_menus = db.query(models.Menu).all()
    return {x.name: {
        'Breakfast': x.breakfast,
        'Lunch': x.lunch,
        'Dinner': x.dinner,
        'Calories': x.calorie,
        'Fat': x.fat,
        'Carbs': x.carbohydrate,
        'Protein': x.protein,
    } for x in all_menus}

# Menu Feature
def get_menu_features(db: Session):
    return db.query(models.MenuFeature).order_by(models.MenuFeature.menu_id).all()
