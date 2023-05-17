from sqlalchemy.orm import Session
from sqlalchemy import func

import models, schemas

from routers.user_feature import crud

# User State
def get_user_state_by_line_id(db: Session, line_id: str):
    return db.query(models.UserState).filter(models.UserState.line_id == line_id).first()

def create_user_state(db: Session, user_state: schemas.UserStateCreate):
    db_user_state = models.UserState(**user_state.dict())
    db.add(db_user_state)
    db.commit()
    db.refresh(db_user_state)
    return db_user_state

def update_user_state_by_line_id(db:Session, line_id: str, state: str):
    """
    Update user state by LINE ID
    None -> registered -> recommendation_sent -> menu_recognized -> image_categorized -> registered -> ...
    """
    
    user_state = db.query(models.UserState).filter(models.UserState.line_id == line_id).first()
    if user_state:
        user_state.state = state
        db.commit()

    return user_state

# User
def get_user(db: Session, user_id: int):
    return db.query(models.User).filter(models.User.id == user_id).first()

def get_users(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.User).order_by(models.User.id).all()

def get_user_by_line_id(db: Session, line_id: str):
    return db.query(models.User).filter(models.User.line_id == line_id).first()

def create_user(db: Session, user: schemas.UserCreate):
    # db_user = models.User(**user.dict())
    db_user = models.User(
        line_id=user.line_id,
        name=user.name,
        status=user.status,
        birth_date=user.birth_date,
        gender=user.gender,
        weight=user.weight,
        height=user.height,
        picture_url=user.picture_url,
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)

    # Create user state
    db_user_state = create_user_state(db, schemas.UserStateCreate(user_id=db_user.id, line_id=user.line_id, state=user.state))
    # Create user features
    db_user_features = crud.create_multiple_user_features(db, schemas.UserMultipleFeatuerCreate(user_id=db_user.id, feature_ids=user.feature_ids))

    return db_user

def update_user_by_line_id(db: Session, weight: float, height: float, line_id: str):
    """Update user by LINE user ID."""
    
    user = db.query(models.User).filter(models.User.line_id == line_id).first()
    if user:
        user.weight = weight
        user.height = height
        db.commit()

    return user
    