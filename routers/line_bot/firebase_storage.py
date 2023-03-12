import os
import base64
import uuid
import numpy as np
from io import BytesIO
from PIL import Image
import firebase_admin
from firebase_admin import credentials, storage
from dotenv import load_dotenv, find_dotenv


class FirebaseStorage:
    
    # Load .env variables
    load_dotenv(find_dotenv())
    REALTIME_DB_URL = os.getenv("REALTIME_DB_URL")
    FIREBASE_PRIV_KEY = os.getenv("FIREBASE_PRIV_KEY")
    
    
    def __init__(self):
        
        creds = credentials.Certificate(self.FIREBASE_PRIV_KEY)
        firebase_admin.initialize_app(
            creds,
            {
                'storageBucket': 'eatwise-a3ea2.appspot.com'
                }
        )
    
    
    def upload_retrain_image(self, label, img_path):
        
        bucket = storage.bucket()
        uniq_id = uuid.uuid4()
        uploaded_name = f"{label}_{uniq_id}.jpg"
        uploaded_path = f"retrain_images/{label}/{uploaded_name}"
        blob = bucket.blob(uploaded_path)
        blob.upload_from_filename(img_path)

