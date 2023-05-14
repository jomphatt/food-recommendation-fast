from sqlalchemy.orm import Session

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