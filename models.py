from sqlalchemy import Column, ForeignKey, Integer, String, Float, DateTime
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

from database import Base


class Order(Base):
    __tablename__ = "orders"

    id = Column(Integer, primary_key=True, index=True, nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"))
    menu_id = Column(Integer, ForeignKey("menus.id"))
    create_at = Column(DateTime(timezone=True), server_default=func.now())

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
    picture_url = Column(String)
    create_at = Column(DateTime(timezone=True), server_default=func.now())

    menus = relationship("Order", back_populates="user")

class Menu(Base):
    __tablename__ = "menus"

    id = Column(Integer, primary_key=True, index=True, nullable=False)
    name = Column(String, nullable=False)
    calorie = Column(Float, nullable=False)
    protein = Column(Float, nullable=False)
    fat = Column(Float, nullable=False)
    carbohydrate = Column(Float, nullable=False)
    create_at = Column(DateTime(timezone=True), server_default=func.now())

    users = relationship("Order", back_populates="menu")