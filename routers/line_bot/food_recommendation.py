# Import general libraries
import os
import random
import requests
from dotenv import load_dotenv, find_dotenv


# Load environment variables
load_dotenv(find_dotenv())

# Declare database URLs
# TODO: 
# Put the databases in a directory, e.g. /databases/menus and put the base URL in .env.
# API_ENDPOINT_URL = os.getenv("API_ENDPOINT_URL")
# BASE_DB_URL = API_ENDPOINT_URL + "databases/"
BASE_DB_URL = "https://c6b0-171-98-30-190.ap.ngrok.io/"
MENU_DB_URL = BASE_DB_URL + "menus/"
ORDER_DB_URL = BASE_DB_URL + "orders/"
USER_DB_URL = BASE_DB_URL + "users/"


class FoodRecommendation:
    
    def __init__(self):
        pass


    # TODO: Replace random.sample() with a real recommendation algorithm.
    def recommend_menus(self, n_menus=5) -> list:
        """Recommend menus.

        Args:
            n_menus (int): Number of menus to be recommended.
        
        Returns:
            recommended_menus (list): List of recommended menus. Each menu is a dictionary.
        """
        
        r = requests.get(MENU_DB_URL)
        menu_db = r.json()
        menu_ids = [id for id in menu_db.keys()]
        recommended_menu_ids = random.sample(menu_ids, n_menus)
        recommended_menus = [menu_db[id] for id in recommended_menu_ids]
        return recommended_menus

