# Import general libraries
import random
from dotenv import load_dotenv, find_dotenv

# Import database libraries
import database
import routers.menu.crud as menu_crud

# Initialize database session
db = database.SessionLocal()

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
        
        menu_db = menu_crud.get_menus(db)
        menu_ids = [id for id in menu_db]
        recommended_menu_ids = random.sample(menu_ids, n_menus)
        recommended_menus = [menu_db[id] for id in recommended_menu_ids]
        return recommended_menus

