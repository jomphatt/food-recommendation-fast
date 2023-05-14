from typing import Union, List

from pydantic import BaseModel
from datetime import datetime

class MenuBase(BaseModel):
    name: str
    calorie: float
    protein: float
    fat: float
    carbohydrate: float

class MenuCreate(MenuBase):
    pass

class Menu(MenuBase):
    id: int
    create_at: datetime

    class Config:
        orm_mode = True
        
class UserBase(BaseModel):
    line_id: str
    name: str
    status: str
    birth_date: datetime
    gender: str
    weight: float
    height: float
    picture_url: str

class UserCreate(UserBase):
    pass

class User(UserBase):
    id: int
    create_at: datetime

    class Config:
        orm_mode = True

class OrderBase(BaseModel):
    user_id: int
    menu_id: int

class OrderCreate(OrderBase):
    pass

class Order(OrderBase):
    id: int
    create_at: datetime
    user: User
    menu: Menu

    class Config:
        orm_mode = True

class FeatureBase(BaseModel):
    name: str

class FeatureCreate(FeatureBase):
    pass

class Feature(FeatureBase):
    id: int
    create_at: datetime

    class Config:
        orm_mode = True

class UserFeatureBase(BaseModel):
    user_id: int
    feature_id: int

class UserFeatureCreate(UserFeatureBase):
    pass

class UserFeature(UserFeatureBase):
    id: int
    create_at: datetime
    user: User
    feature: Feature

    class Config:
        orm_mode = True