from sqlalchemy.orm import Session
from sqlalchemy import func, and_
import models, schemas
from datetime import datetime, timedelta

def get_order(db: Session, order_id: int):
    return db.query(models.Order).filter(models.Order.id == order_id).first()

def get_lastest_order(db: Session, user_id: int):
    return db.query(models.Order).filter(models.Order.user_id == user_id).order_by(models.Order.create_at.desc()).first()

def get_order_by_user_id(db: Session, user_id: int):
    return db.query(models.Order).filter(models.Order.user_id == user_id).all()

def get_daily_summary(db: Session, user_id: int):
    
    # Get start of day    
    current_time_utc = datetime.utcnow()
    current_time_gmt_7 = current_time_utc + timedelta(hours=7)
    start_of_day = current_time_gmt_7.replace(hour=0, minute=0, second=0, microsecond=0)
    
    # Query nutrition summary since start of day
    query_result = (
        db.query(
            func.array_agg(models.Order.menu_id).label("set_menu_id"),
            func.sum(models.Menu.protein).label('sum_protein'),
            func.sum(models.Menu.carbohydrate).label('sum_carbohydrate'),
            func.sum(models.Menu.fat).label('sum_fat'),
            func.sum(models.Menu.calorie).label('sum_calorie')
        )
        .filter(and_(
            models.Order.create_at >= start_of_day, 
            models.Order.user_id == user_id
            )
        )
        .join(models.Menu, models.Order.menu_id == models.Menu.id)
        .group_by(models.Order.user_id)
        .all()
    )
    
    return query_result

def get_top_menus_by_user(db: Session, user_id: int, top_n: int):
    query_result = (
        db.query(
            models.Menu.name,
            models.Menu.calorie,
            func.count(models.Order.menu_id).label('count_menu_id')
        )
        .filter(models.Order.user_id == user_id)
        .group_by(models.Menu.name, models.Menu.calorie)
        .order_by(func.count(models.Order.menu_id).desc())
        .join(models.Menu, models.Order.menu_id == models.Menu.id)
        .limit(top_n)
        .all()
    )
    return query_result

def get_orders(db: Session):
    return db.query(models.Order).all()

def create_order(db: Session, order: schemas.OrderCreate):
    db_order = models.Order(**order.dict())
    db.add(db_order)
    db.commit()
    db.refresh(db_order)
    return db_order