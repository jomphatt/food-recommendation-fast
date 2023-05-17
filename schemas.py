from typing import Union, List

from pydantic import BaseModel
from datetime import datetime

class MenuBase(BaseModel):
    name: str
    calorie: float
    protein: float
    fat: float
    carbohydrate: float
    breakfast: float
    lunch: float
    dinner: float

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
    state: str
    feature_ids: List[int]

class User(UserBase):
    id: int
    create_at: datetime

    class Config:
        orm_mode = True

class OrderBase(BaseModel):
    user_id: int
    menu_id: int
    rating: Union[int, None]

class OrderCreate(OrderBase):
    create_at: datetime

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

class UserMultipleFeatuerCreate(BaseModel):
    user_id: int
    feature_ids: List[int]

class UserFeature(UserFeatureBase):
    id: int
    create_at: datetime
    # user: User
    # feature: Feature

    class Config:
        orm_mode = True

class UserStateBase(BaseModel):
    user_id: int
    line_id: str
    state: str

class UserStateCreate(UserStateBase):
    pass

class UserState(UserStateBase):
    id: int
    update_at: datetime
    create_at: datetime

    class Config:
        orm_mode = True
        
class MenuFeatureBase(BaseModel):
    menu_id: int
    spicy: int
    high_sugar: int
    high_fat: int
    high_calorie: int
    is_light: int
    is_fried: int
    contain_water: int
    has_vegetable: int
    high_sodium: int
    high_protein: int
    high_carbohydrate: int
    high_cholesterol: int
    has_chicken: int
    has_pork: int
    has_noodle: int
    high_price: int

class MenuFeatureCreate(MenuFeatureBase):
    pass

class MenuFeature(MenuFeatureBase):
    class Config:
        orm_mode = True