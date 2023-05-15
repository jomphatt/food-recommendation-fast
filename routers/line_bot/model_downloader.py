# Import general libraries
import os
from dotenv import load_dotenv, find_dotenv

# Import Azure Blob Storage libraries
from azure.storage.blob import BlobServiceClient


class ModelDownloader():
    
    # Load environment variables
    load_dotenv(find_dotenv())
    
    # Declare Azure Blob Storage credentials
    AZURE_ACCOUNT_KEY = os.getenv("AZURE_ACCOUNT_KEY")
    AZURE_ACCOUNT_NAME = os.getenv("AZURE_ACCOUNT_NAME")
    
    # Declare Azure Blob Storage container name
    CONTAINER_NAME = "models"
    food_nonfood_dir = "food_nonfood/"
    food_recognition_dir = "food_recognition/"
    
    # Initialize BlobServiceClient and ContainerClient
    connection_string = f"DefaultEndpointsProtocol=https;AccountName={AZURE_ACCOUNT_NAME};AccountKey={AZURE_ACCOUNT_KEY};EndpointSuffix=core.windows.net"
    blob_service_client = BlobServiceClient.from_connection_string(connection_string)
    container_client = blob_service_client.get_container_client(CONTAINER_NAME)
    
    
    def __download_blob(self, blob_name: str):

        blob_client = self.blob_service_client.get_blob_client(container=self.container_name, blob=blob_name)
        local_path = f"./assets/models/{blob_name}"
        with open(local_path, 'wb') as local_path:
            local_path.write(blob_client.download_blob().readall())
    
    
    def download_latest_model(self, model_name: str):
        
        if model_name == "food_nonfood":
            model_dir = self.food_nonfood_dir
        elif model_name == "food_recognition":
            model_dir = self.food_recognition_dir
        
        latest_creation_time = None
        for blob in self.container_client.list_blobs():
            if model_dir in blob.name:
                creation_time = blob.properties.creation_time
                if not latest_creation_time or (creation_time > latest_creation_time):
                    latest_model = blob.name
                    latest_creation_time = creation_time
        
        self.__download_blob(latest_model)

