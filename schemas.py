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
