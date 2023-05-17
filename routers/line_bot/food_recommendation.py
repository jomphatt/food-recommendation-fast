# Import general libraries
import random
import numpy as np
import pandas as pd
from dotenv import load_dotenv, find_dotenv
import pickle

# Import LightFM and other libraries for recommendation
from lightfm import LightFM
from lightfm.evaluation import precision_at_k, recall_at_k, auc_score
from sklearn.preprocessing import OneHotEncoder, MinMaxScaler
from scipy.sparse import csr_matrix, hstack
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.preprocessing import OneHotEncoder, MinMaxScaler
from sklearn.metrics.pairwise import cosine_similarity

# Import database 
import database
import routers.menu.crud as menu_crud
import routers.order.crud as order_crud
import routers.user.crud as user_crud


# Initialize database session
db = database.SessionLocal()


class FoodRecommendation:
       
    def __init__(self):
        pass
    
    def train_model(self, interaction_matrix, user_features, food_features):
        # Create the LightFM model
        model = LightFM(loss='warp', no_components=32)  # You can experiment with different loss functions and hyperparameters

        # Fit the model on your interaction matrix and user/food features
        model.fit(interaction_matrix, user_features=user_features, item_features=food_features, epochs=30)
        
        with open('assets/models/rec_model.pickle', 'wb') as fle:
            pickle.dump(model, fle, protocol=pickle.HIGHEST_PROTOCOL)
            
    def load_model(self):
        with open('assets/models/rec_model.pickle', 'rb') as fle:
            model = pickle.load(fle)
            
        return model
    
    # Function to return the top n items in a dictionary sorted by value
    def top_n_items(self, dictionary, n):
        sorted_items = sorted(dictionary.items(), key=lambda x: x[1]['score'], reverse=True)
        return dict(sorted_items[:n])
    
    # Function to calculate b value for each nutrient based on min and max nutrient values in the dataset
    def calculate_b(self, nutrient, nutrient_data, nutritional_goal_left, a1, a2, MinPositiveScore):
        min_nutrient = min([nutrient_data[food_name][nutrient] for food_name in nutrient_data])
        max_nutrient = max([nutrient_data[food_name][nutrient] for food_name in nutrient_data])

        nutrient_scores = []
        for total_nutrient in [min_nutrient, max_nutrient]:
            nutrient_score = -a1 * (total_nutrient - nutritional_goal_left[nutrient])**2 if (nutritional_goal_left[nutrient] - total_nutrient) >= 0 else -a2 * (total_nutrient - nutritional_goal_left[nutrient])**2
            nutrient_scores.append(nutrient_score)

        MostNegativeScore = min(nutrient_scores)
        b_nutrient = abs(MostNegativeScore) + MinPositiveScore

        return b_nutrient
    
    
    def dynamic_food_recommend(self, model, interaction_matrix, user_id, user_features, food_id, food_names, food_features, nutrient_data, nutritional_goal_left, meal_time, n_recommendations=5, a1=0.001, a2=0.002, w1=0.3, w2=0.2, w3=0.3, w4=0.2, MinPositiveScore = 1):

        # Get the index of the user in the interaction matrix
        user_index = user_id

        # Predict scores for all food items for the user
        scores = model.predict(user_index, np.arange(interaction_matrix.shape[1]), user_features=user_features, item_features=food_features)

        # Calculate the cosine similarity matrix for food items using their features
        similarities = cosine_similarity(food_features)

        # Define the minimum and maximum values for normalization
        b_values = {nutrient: self.calculate_b(nutrient, nutrient_data, nutritional_goal_left, a1, a2, MinPositiveScore) for nutrient in ['Calories', 'Fat', 'Carbs', 'Protein']}
        MinNutrientScore = {nutrient: -b_values[nutrient] for nutrient in ['Calories', 'Fat', 'Carbs', 'Protein']}
        MaxNutrientScore = b_values

        MinPreference = min(scores)
        MaxPreference = max(scores)

        MinSimilarity = 0
        MaxSimilarity = 1

        MinTimeScore = 0
        MaxTimeScore = 1

        final_dict = nutrient_data
        for i, food_name in enumerate(food_names):
            # Normalize the preference rating
            PreferenceRating = scores[i]
            NormalizedPreferenceRating = (PreferenceRating - MinPreference) / (MaxPreference - MinPreference)

            # Normalize the similarity penalty
            if food_id < 0:
                NormalizedSimilarityPenalty = 0
            else:
                SimilarityPenalty = similarities[food_id][i]
                NormalizedSimilarityPenalty = (SimilarityPenalty - MinSimilarity) / (MaxSimilarity - MinSimilarity)

            # Calculate and normalize nutrient scores for each nutrient
            nutrient_scores = []
            for nutrient in ['Calories', 'Fat', 'Carbs', 'Protein']:
                total_nutrient = nutrient_data[food_name][nutrient]
                nutrient_score = -a1 * (total_nutrient - nutritional_goal_left[nutrient])**2 + b_values[nutrient] if (nutritional_goal_left[nutrient] - total_nutrient) >= 0 else -a2 * (total_nutrient - nutritional_goal_left[nutrient])**2 + b_values[nutrient]
                normalized_nutrient_score = (nutrient_score - MinNutrientScore[nutrient]) / (MaxNutrientScore[nutrient] - MinNutrientScore[nutrient])
                nutrient_scores.append(normalized_nutrient_score)

            # Calculate the average nutrient score
            avg_nutrient_score = sum(nutrient_scores) / len(nutrient_scores)

            # Get the time-based score and normalize it
            TimeScore = nutrient_data[food_name][meal_time]
            NormalizedTimeScore = (TimeScore - MinTimeScore) / (MaxTimeScore - MinTimeScore)

            # Calculate the final score for each food item
            score = w1 * NormalizedPreferenceRating - w2 * NormalizedSimilarityPenalty + w3 * avg_nutrient_score + w4 * NormalizedTimeScore

            # Update the final_dict with the calculated score
            final_dict[food_name]['score'] = score

        # Get the top n recommendations based on the final scores
        top_n = n_recommendations
        top_n_food_data = self.top_n_items(final_dict, top_n)
        print(top_n_food_data)
        
        return top_n_food_data


    def mock_recommend_menus(self, n_menus=5) -> list:
        """Recommend menus.

        Args:
            n_menus (int): Number of menus to be recommended.
        
        Returns:
            recommended_menus (list): List of recommended menus. Each menu is a dictionary.
        """
        
        menu_db = menu_crud.get_menus(db)
        menu_ids = [id for id in menu_db]
        recommended_menu_ids = random.sample(menu_ids, n_menus)
        recommended_menus = [menu_db[id] for id in recommended_menu_ids]
        return recommended_menus
