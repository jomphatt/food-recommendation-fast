# Import packages for food recognition
import numpy as np
import pandas as pd
from PIL import Image
from tensorflow.keras.models import Model, model_from_json
from tensorflow.keras.preprocessing import image
from tensorflow.keras.applications.vgg19 import preprocess_input as preprocess_input_VGG19_model

# Import Firebase Storage class
from routers.line_bot.firebase_storage import FirebaseStorage

class FoodRecognition:
    
    # Food labels
    prediction_classes = {
        0:'chicken_noodle',
        1: 'dumplings',
        2: 'fried_chicken',
        3: 'fried_chicken_salad_sticky_rice',
        4: 'fried_pork_curry_rice',
        5: 'grilled_pork_with_sticky_rice',
        6: 'lek_tom_yam',
        7: 'mama_namtok',
        8: 'pork_blood_soup',
        9: 'pork_congee',
        10: 'pork_suki',
        11: 'rice_scramble_egg',
        12: 'rice_topped_with_stir_fried_pork_and_basil',
        13: 'rice_with_roasted_pork',
        14: 'roasted_red_pork_noodle',
        15: 'sliced_grilled_pork_salad',
        16: 'steamed_rice_with_chicken',
        17: 'steamed_rice_with_fried_chicken',
        18: 'stir_fried_rice_noodles_with_chicken',
        19: 'stir_fried_rice_noodles_with_soy_sauce_and_pork'
    }
    
    # This is how the dict supposes to look like once Pann finished training the new model.
    # Also, we can store this dict in a JSON file, so the code looks cleaner.
    actual_classes = {
        'menu_1': 'chicken_noodles',
        'menu_2': 'fried_chicken_with_sticky_rice',
        'menu_3': 'fried_pork_curry_with_rice',
        'menu_4': 'grilled_pork_with_sticky_rice',
        'menu_5': 'lek_tom_yam',
        'menu_6': 'mama_nam_tok',
        'menu_7': 'pork_blood_soup',
        'menu_8': 'pork_congee',
        'menu_9': 'pork_suki',
        'menu_10': 'rice_topped_with_stir_fried_pork_and_basil', # Should be 'stir_fried_pork_and_basil_with_rice'
        'menu_11': 'rice_with_roasted_pork', # Should be 'roasted_pork_with_rice'
        'menu_12': 'roasted_red_pork_dumplings',
        'menu_13': 'roasted_red_pork_noodle',
        'menu_14': 'scrambled_egg_with_rice',
        'menu_15': 'sliced_grilled_pork_salad',
        'menu_16': 'spicy_fried_chicken_with_sticky_rice',
        'menu_17': 'steamed_rice_with_chicken',
        'menu_18': 'steamed_rice_with_fried_chicken',
        'menu_19': 'stir_fried_rice_noodles_with_chicken',
        'menu_20': 'stir_fried_rice_noodles_with_soy_sauce_and_pork'
    }

    # Paths to the VGG-19 model
    vgg19_json_path = "./assets/models/VGG19_model.json"
    vgg19_h5_path = "./assets/models/VGG19_model.h5"
    
    
    def predict(self, img_path):
        """Predict a menu from a file path to a food image.

        Args:
            img_path (str): Food image file path

        Returns:
            prediction (str): Predicted menu
        """
        
        food_img = image.load_img(img_path, target_size=(224, 224))

        img_arr = image.img_to_array(food_img)
        img_arr = np.expand_dims(img_arr, axis=0)
        img_arr = preprocess_input_VGG19_model(img_arr)
        
        json_file = open(self.vgg19_json_path, 'r')
        model_json = json_file.read()
        json_file.close()
        
        model = model_from_json(model_json)
        model.load_weights(self.vgg19_h5_path) # Load weights into the model

        y_pred = model.predict(img_arr, batch_size=1)
        y_pred = np.argmax(y_pred)
        prediction = self.prediction_classes[y_pred]
        
        return prediction
    
    