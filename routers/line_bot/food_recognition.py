import numpy as np
import pandas as pd
from PIL import Image
from tensorflow.keras.models import Model, model_from_json
from tensorflow.keras.preprocessing import image
from tensorflow.keras.applications.vgg19 import preprocess_input as preprocess_input_VGG19_model

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
    
    # Paths to the VGG-19 model
    vgg19_json_path = "./assets/models/VGG19_model.json"
    vgg19_h5_path = "./assets/models/VGG19_model.h5"
    
    def predict(self, img_path):
        """
        Give a prediction of an input food image.
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
        return self.prediction_classes[y_pred]
    
    