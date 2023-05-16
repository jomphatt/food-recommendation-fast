import io
import os
import uuid
import datetime
import firebase_admin
from PIL import Image
from firebase_admin import credentials, storage
from dotenv import load_dotenv, find_dotenv


class FirebaseStorage:
    
    # Load .env variables
    load_dotenv(find_dotenv())
    FIREBASE_PRIV_KEY = os.getenv("FIREBASE_PRIV_KEY")
    
    
    def __init__(self):
        """Initialize Firebase Storage."""
        
        # Initialize Firebase Storage client with Firebase private key
        creds = credentials.Certificate(self.FIREBASE_PRIV_KEY)
        firebase_admin.initialize_app(
            creds,
            {
                'storageBucket': 'eatwise-a3ea2.appspot.com'
            }
        )
    
    
    def upload_preprocessed_image(self, menu_id: int, img_byte: bytes, is_preprocessed: bool = True):
        """Upload preprocessed image to Firebase Storage for retraining."""
        
        if not is_preprocessed:
            # Convert image byte to PIL image and resize it
            img_pil = Image.open(img_byte)
            img_pil = img_pil.resize((224, 224))

            # Convert the PIL Image to a byte stream
            img_byte = io.BytesIO()
            img_pil.save(img_byte, format='JPEG')
            img_byte = img_byte.getvalue()

        bucket = storage.bucket()
        uniq_id = uuid.uuid4()
        uploaded_name = f"{menu_id}_{uniq_id}.jpg"
        uploaded_path = f"retrain_images/{menu_id}/{uploaded_name}"
        blob = bucket.blob(uploaded_path)
        blob.upload_from_string(
            img_byte,
            content_type='image/jpeg'
        )

    def upload_uncategorized_image(self, line_user_id: str, img_byte: bytes):
        
        bucket = storage.bucket()
        uniq_id = uuid.uuid4()
        uploaded_name = f"{line_user_id}_{uniq_id}.jpg"
        uploaded_path = f"retrain_images/uncategorized/{uploaded_name}"
        blob = bucket.blob(uploaded_path)
        blob.upload_from_string(
            img_byte,
            content_type='image/jpeg'
        )


    def get_image_urls(self, firebase_img_path):
        """Get image URL from Firebase Storage."""

        bucket = storage.bucket()
        blob = bucket.blob(firebase_img_path)
        url = blob.generate_signed_url(expiration=datetime.timedelta(hours=1))
        return url

