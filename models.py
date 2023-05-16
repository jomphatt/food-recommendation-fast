from sqlalchemy import Column, ForeignKey, Integer, String, Float, DateTime
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

from database import Base


class Order(Base):
    __tablename__ = "orders"

    id = Column(Integer, primary_key=True, index=True, nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"))
    menu_id = Column(Integer, ForeignKey("menus.id"))
    rating = Column(Integer, nullable=True)
    create_at = Column(DateTime(timezone=True), server_default=func.now()) # TODO: Change all time-related properties to UTC

    user = relationship("User", back_populates="menus")
    menu = relationship("Menu", back_populates="users")

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True, nullable=False)
    line_id = Column(String, unique=True, index=True)
    name = Column(String, nullable=False)
    status = Column(String, nullable=False, server_default='recommend')
    birth_date = Column(DateTime(timezone=True), nullable=False)
    gender = Column(String, nullable=False)
    weight = Column(Float, nullable=False)
    height = Column(Float, nullable=False)
    picture_url = Column(String)
    create_at = Column(DateTime(timezone=True), server_default=func.now())

    menus = relationship("Order", back_populates="user")
    features = relationship("UserFeature", back_populates="user")
    state = relationship("UserState", uselist=False, back_populates="user")

class Menu(Base):
    __tablename__ = "menus"

    id = Column(Integer, primary_key=True, index=True, nullable=False)
    name = Column(String, nullable=False)
    calorie = Column(Float, nullable=False)
    protein = Column(Float, nullable=False)
    fat = Column(Float, nullable=False)
    carbohydrate = Column(Float, nullable=False)
    breakfast = Column(Float, nullable=True)
    lunch = Column(Float, nullable=True)
    dinner = Column(Float, nullable=True)
    create_at = Column(DateTime(timezone=True), server_default=func.now())

    users = relationship("Order", back_populates="menu")
    feature = relationship("MenuFeature", uselist=False, back_populates="menu")
    
class MenuFeature(Base):
    __tablename__ = "menu_features"
    
    menu_id = Column(Integer, ForeignKey("menus.id"), primary_key=True, index=True, nullable=False)
    spicy = Column(Integer, nullable=False)
    high_sugar = Column(Integer, nullable=False)
    high_fat = Column(Integer, nullable=False)
    high_calorie = Column(Integer, nullable=False)
    is_light = Column(Integer, nullable=False)
    is_fried = Column(Integer, nullable=False)
    contain_water = Column(Integer, nullable=False)
    has_vegetable = Column(Integer, nullable=False)
    high_sodium = Column(Integer, nullable=False)
    high_protein = Column(Integer, nullable=False)
    high_carbohydrate = Column(Integer, nullable=False)
    high_cholesterol = Column(Integer, nullable=False)
    has_chicken = Column(Integer, nullable=False)
    has_pork = Column(Integer, nullable=False)
    has_noodle = Column(Integer, nullable=False)
    high_price = Column(Integer, nullable=False)
    
    menu = relationship("Menu", back_populates="feature")

class Feature(Base):
    __tablename__ = "features"

    id = Column(Integer, primary_key=True, index=True, nullable=False)
    name = Column(String, nullable=False)
    create_at = Column(DateTime(timezone=True), server_default=func.now())

    users = relationship("UserFeature", back_populates="feature")

class UserFeature(Base):
    __tablename__ = "user_features"

    id = Column(Integer, primary_key=True, index=True, nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"))
    feature_id = Column(Integer, ForeignKey("features.id"))
    create_at = Column(DateTime(timezone=True), server_default=func.now())

    user = relationship("User", back_populates="features")
    feature = relationship("Feature", back_populates="users")

class UserState(Base):
    __tablename__ = "user_states"

    id = Column(Integer, primary_key=True, index=True, nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"))
    line_id = Column(String, nullable=False)
    state = Column(String, nullable=False)
    update_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now()) 
    create_at = Column(DateTime(timezone=True), server_default=func.now())

    user = relationship("User", back_populates="state")