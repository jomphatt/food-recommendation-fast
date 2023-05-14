from sqlalchemy.orm import Session

import models, schemas

def get_feature(db: Session, feature_id: int):
    return db.query(models.Feature).filter(models.Feature.id == feature_id).first()

def get_feature_by_name(db: Session, name: str):
    return db.query(models.Feature).filter(models.Feature.name == name).first()

def get_features(db: Session, skip: int = 0, limit: int = 100):
    all_features = db.query(models.Feature).offset(skip).limit(limit).all()
    return all_features

def create_feature(db: Session, feature: schemas.FeatureCreate):
    db_feature = models.Feature(**feature.dict())
    db.add(db_feature)
    db.commit()
    db.refresh(db_feature)
    return db_feature