from sqlalchemy.orm import Session
from sqlalchemy import text

import models, schemas

def get_user_feature(db: Session, user_feature_id: int):
    return db.query(models.UserFeature).filter(models.UserFeature.id == user_feature_id).first()

def get_user_feature_by_user_id(db: Session, user_id: int):
    return db.query(models.UserFeature).filter(models.UserFeature.user_id == user_id).all()

def get_user_feature_by_line_id(db: Session, line_id: str):
    return db.query(models.UserFeature).filter(models.UserFeature.user.has(line_id=line_id)).all()

def get_user_features(db: Session, skip: int = 0, limit: int = 100):
    all_user_features = db.query(models.UserFeature).offset(skip).limit(limit).all()
    return all_user_features

def get_user_features_flag(db: Session):
    query = text("""
        select cheap, chicken, fried, pork, salty, soup, spicy, steam, sweet, vegetable
        from (
        select user_id,
            sum(case when feature_id = 1 then 1 else 0 end) as "cheap",
            sum(case when feature_id = 2 then 1 else 0 end) as "chicken",
            sum(case when feature_id = 3 then 1 else 0 end) as "fried",
            sum(case when feature_id = 4 then 1 else 0 end) as "pork",
            sum(case when feature_id = 5 then 1 else 0 end) as "salty",
            sum(case when feature_id = 6 then 1 else 0 end) as "soup",
            sum(case when feature_id = 7 then 1 else 0 end) as "spicy",
            sum(case when feature_id = 8 then 1 else 0 end) as "steam",
            sum(case when feature_id = 9 then 1 else 0 end) as "sweet",
            sum(case when feature_id = 10 then 1 else 0 end) as "vegetable"
        from user_features uf 
        group by user_id 
        order by user_id
        ) as user_features;
    """)
    
    result = db.execute(query)
    return result.fetchall()

def create_user_feature(db: Session, user_feature: schemas.UserFeatureCreate):
    db_user_feature = models.UserFeature(**user_feature.dict())
    db.add(db_user_feature)
    db.commit()
    db.refresh(db_user_feature)
    return db_user_feature

def create_multiple_user_features(db: Session, user_multiple_features: schemas.UserMultipleFeatuerCreate):
    db_user_features = []
    user_id = user_multiple_features.user_id
    feature_ids = user_multiple_features.feature_ids

    for feature_id in feature_ids:
        db_user_feature = models.UserFeature(user_id=user_id, feature_id=feature_id)
        db.add(db_user_feature)
        db_user_features.append(db_user_feature)
    
    db.commit()
    db.refresh(db_user_feature)
    return db_user_features