import os
import uuid
import datetime
import firebase_admin
from firebase_admin import credentials, storage
from dotenv import load_dotenv, find_dotenv


class FirebaseStorage:
    
    # Load .env variables
    load_dotenv(find_dotenv())
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


    def get_image_urls(self, firebase_img_path):

        bucket = storage.bucket()
        blob = bucket.blob(firebase_img_path)
        url = blob.generate_signed_url(expiration=datetime.timedelta(hours=1))
        return url

