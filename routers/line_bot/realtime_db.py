import os
import base64
import numpy as np
from io import BytesIO
from PIL import Image
import firebase_admin
from firebase_admin import credentials, db
from dotenv import load_dotenv, find_dotenv


class RealtimeDB:
    
    # Load .env variables
    load_dotenv(find_dotenv())
    REALTIME_DB_URL = os.getenv("REALTIME_DB_URL")
    FIREBASE_PRIV_KEY = os.getenv("FIREBASE_PRIV_KEY")
    
    def __init__(self):
        creds = credentials.Certificate(self.FIREBASE_PRIV_KEY)
        firebase_admin.initialize_app(
            creds, 
            {
                'databaseURL': self.REALTIME_DB_URL
            }
        )
    
    def upload(self, label, img_arr):
        
        binary_data = img_arr.tostring() # Convert numpy array to binary data
        b64_data = base64.b64encode(binary_data).decode('utf-8') # Base64-encode binary data to store it in Firebase Realtime DB
        ref = db.reference('images')
        ref.child(label).set(b64_data)


    def download(self, label, mode="array"):
        
        ref = db.reference('images')
        b64_data = ref.child(label).get()
        binary_data = base64.b64decode(b64_data.encode('utf-8'))
        image = Image.open(BytesIO(binary_data))
        if mode == "array":
            img_arr = np.array(image)
            return img_arr
        elif mode == "file":
            image.save('./assets/test.jpg')

