from fastapi import APIRouter, Depends, HTTPException, Request, Header
from sqlalchemy.orm import Session
from typing import List, Dict

import schemas, database
from routers.menu import crud

from scipy.sparse import csr_matrix, hstack
from sklearn.preprocessing import MinMaxScaler
import pandas as pd

import routers.menu.crud as menu_crud
import routers.order.crud as order_crud
import routers.user.crud as user_crud
import routers.user_feature.crud as user_feature_crud

from routers.line_bot.food_recommendation import FoodRecommendation

router = APIRouter(
    prefix="/recommend",
    tags=["recommend"],
    responses={404: {"description": "Not found"}}
)

food_recommendation = FoodRecommendation()

# Dependency
def get_db():
    db = database.SessionLocal()
    try:
        yield db
    finally:
        db.close()
        
        
@router.post("/")
def train_model(db: Session = Depends(get_db)):
    gender_mapping = {
        "Male": (0, 1),
        "Female": (1, 0),
        "Other": (0, 0),
        "Prefer not to say": (0, 0)
    }
    sc = MinMaxScaler()
    # User features
    users = user_crud.get_users(db=db)
    user_age_height_weight_norm = list(map(tuple, sc.fit_transform([[2023 - user.birth_date.year, user.height, user.weight] for user in users])))

    user_preferences = user_feature_crud.get_user_features_flag(db=db)
    user_predference_features = [(x.cheap, x.chicken, x.fried, x.pork, x.salty, x.soup, x.spicy, x.steam, x.sweet, x.vegetable) for x in user_preferences]

    user_features_sparse = csr_matrix([numerical + (gender_mapping[user.gender]) + prefer for numerical, prefer, user in zip(user_age_height_weight_norm, user_predference_features, users)])

    # Food features
    menu_features = menu_crud.get_menu_features(db=db)
    menu_features_sparse = csr_matrix([(menu.spicy, menu.high_sugar, menu.high_fat, menu.high_calorie, menu.is_light, menu.is_fried, menu.contain_water, menu.has_vegetable, menu.high_sodium, menu.high_protein, menu.high_carbohydrate, menu.high_cholesterol, menu.has_chicken, menu.has_pork, menu.has_noodle, menu.high_price) for menu in menu_features])

    # Interaction Matrix
    interaction_matrix = order_crud.get_orders(db=db)

    interaction_user = [order.user_id for order in interaction_matrix]
    fill_in_user = [user_id for user_id in range(0, len(users)) if user_id not in interaction_user]
    interaction_user = interaction_user + fill_in_user

    interaction_menu = [order.menu_id for order in interaction_matrix] + ([0.0] * len(fill_in_user))

    interaction_rating = [order.rating for order in interaction_matrix] + ([0.0] * len(fill_in_user))

    interaction_matrix_sparse = csr_matrix(pd.crosstab(interaction_user, interaction_menu, values=interaction_rating, aggfunc='mean').fillna(0))

    print("Start Training")
    model = food_recommendation.train_model(interaction_matrix_sparse, user_features_sparse, menu_features_sparse)
    print("Done")