# Import general libraries
import numpy as np

# Import Keras libraries
from keras.models import Model, model_from_json
from keras.preprocessing import image
from keras.applications.vgg19 import preprocess_input as preprocess_input_vgg19
from keras.applications.inception_v3 import preprocess_input as preprocess_input_inception_v3

# Import Onnx runtime
import onnxruntime as ort


class FoodRecognition:
    
    # TODO: Pull prediction classes from Menu database. 


    # Declare Onnx version of VGG-19 model path for food/non-food classification
    vgg19_model_path = "./assets/models/vgg19_model.onnx"
    
    # Declare Onnx version of InceptionV3 model path for food menu recognition
    inception_v3_model_path = "./assets/models/inception_v3_model.onnx"
    
    
    def __create_onnx_session(self, model_path):
        
        # Load Onnx model
        onnx_session = ort.InferenceSession(model_path)
        
        # Get model input and output names
        input_name = onnx_session.get_inputs()[0].name
        output_name = onnx_session.get_outputs()[0].name
        
        return onnx_session, input_name, output_name

    
    def __preprocess_image(self, img_path):
        
        # Load and resize image
        food_img = image.load_img(img_path, target_size=(224, 224))

        # Convert image to Numpy array and expand its dimension
        img_arr = image.img_to_array(food_img)
        img_arr = np.expand_dims(img_arr, axis=0)
        
        return img_arr
    
    
    def is_food(self, img_path):
        
        # Create Onnx session for VGG-19 model
        vgg19_onnx_session, vgg19_input_name, vgg19_output_name = self.__create_onnx_session(self.vgg19_model_path)
        
        # Preprocess image
        img_arr = self.__preprocess_image(img_path)

        # Predict image
        predictions = vgg19_onnx_session.run([vgg19_output_name], {vgg19_input_name: img_arr})[0]

        # Post-process predictions
        predicted_class = predictions[0][0]

        return predicted_class == 1


    def recognize_menu(self, img_path):
        
        # Create Onnx session for VGG-19 model
        inception_v3_onnx_session, inception_v3_input_name, inception_v3_output_name = self.__create_onnx_session(self.inception_v3_model_path)
        
        # Preprocess image
        img_arr = self.__preprocess_image(img_path)

        # Predict image
        predictions = inception_v3_onnx_session.run([inception_v3_output_name], {inception_v3_input_name: img_arr})[0]

        # Post-process predictions
        predicted_class = np.argmax(predictions)

        return predicted_class

