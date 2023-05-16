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
    
    
    def __move_file(seld, src_path: str, dest_path: str):
        """Move file from source path to destination path in Firebase Storage."""
        
        bucket = storage.bucket()
        src_blob = bucket.blob(src_path)

        # Check if source path exists
        if not src_blob.exists():
            return

        # Copy the source blob to the destination blob
        dest_blob = bucket.blob(dest_path)
        bucket.copy_blob(src_blob, bucket, new_name=dest_path)

        # Check if destination path exists which means the copy was successful
        if not dest_blob.exists():
            return

        # Delete the source blob
        src_blob.delete()
    
    
    def upload_preprocessed_image(self, menu_id: int, img_byte: bytes, is_preprocessed: bool = True):
        """Upload preprocessed image to Firebase Storage for retraining."""
        
        if not is_preprocessed:
            # Convert image byte to PIL image and resize it
            img_pil = Image.open(img_byte)
            img_pil = img_pil.resize((224, 224))

            # Convert the PIL Image to a byte stream
            img_byte = io.BytesIO()
            img_pil.save(img_byte, format='JPEG')
            img_byte.seek(0)
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
        """Upload an image to a folder named 'uncategorized' in Firebase Storage."""
        
        bucket = storage.bucket()
        uniq_id = uuid.uuid4()
        uploaded_name = f"{line_user_id}_{uniq_id}.jpg"
        uploaded_path = f"retrain_images/uncategorized/{uploaded_name}"
        blob = bucket.blob(uploaded_path)
        blob.upload_from_string(
            img_byte,
            content_type='image/jpeg'
        )
        
        
    def categorize_image(self, line_user_id: str, menu_id: int,):
        """Categorize an image in Firebase Storage by moving it from 'uncategorized' folder to a folder named after the menu ID."""
        
        bucket = storage.bucket()
        
        # List all blobs in the 'uncategorized' folder
        blobs = bucket.list_blobs(prefix="retrain_images/uncategorized/")

        # Iterate through blobs and check for matching pattern
        for blob in blobs:
            if blob.name.startswith(f"retrain_images/uncategorized/{line_user_id}_") and blob.name.endswith(".jpg"):
                
                # Move the image to the folder named after the menu ID
                dest_path = f"retrain_images/{menu_id}/" + blob.name.split("/")[-1]
                self.__move_file(src_path=blob.name, dest_path=dest_path)
        

    def get_image_urls(self, firebase_img_path):
        """Get image URL from Firebase Storage."""

        bucket = storage.bucket()
        blob = bucket.blob(firebase_img_path)
        url = blob.generate_signed_url(expiration=datetime.timedelta(hours=1))
        return url

