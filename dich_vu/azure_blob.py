# -*- coding: utf-8 -*-
import os
import logging

logger = logging.getLogger("app.azure_blob")

# Load environment variables
AZURE_CONN_STR = os.getenv("AZURE_STORAGE_CONNECTION_STRING", "")
AZURE_CONTAINER = os.getenv("AZURE_BLOB_CONTAINER_NAME", "giao-trinh-ai-files")

_blob_service_client = None
_container_client = None

def get_container_client():
    global _blob_service_client, _container_client
    if not AZURE_CONN_STR:
        return None
        
    if _container_client is not None:
        return _container_client
        
    try:
        from azure.storage.blob import BlobServiceClient
        _blob_service_client = BlobServiceClient.from_connection_string(AZURE_CONN_STR)
        _container_client = _blob_service_client.get_container_client(AZURE_CONTAINER)
        
        # Ensure container exists
        if not _container_client.exists():
            logger.info(f"Creating Azure Blob container: {AZURE_CONTAINER}")
            _container_client.create_container()
            
        return _container_client
    except Exception as e:
        logger.error(f"Failed to initialize Azure Blob Client: {e}")
        return None

def upload_to_blob(local_path, blob_name):
    """
    Uploads a local file to Azure Blob Storage under the given blob name.
    Returns True if successful, False otherwise.
    """
    if not os.path.exists(local_path):
        logger.warning(f"Local file not found for upload: {local_path}")
        return False
        
    client = get_container_client()
    if client is None:
        logger.info("Azure Blob Storage not configured or failed to init. Skipping upload.")
        return False
        
    try:
        blob_client = client.get_blob_client(blob_name)
        with open(local_path, "rb") as data:
            blob_client.upload_blob(data, overwrite=True)
        logger.info(f"Successfully uploaded {local_path} to Azure Blob: {blob_name}")
        return True
    except Exception as e:
        logger.error(f"Error uploading {local_path} to Azure Blob: {e}")
        return False

def download_from_blob(blob_name, local_path):
    """
    Downloads a file from Azure Blob Storage to a local path.
    Returns True if successful, False otherwise.
    """
    client = get_container_client()
    if client is None:
        logger.info("Azure Blob Storage not configured or failed to init. Skipping download.")
        return False
        
    try:
        blob_client = client.get_blob_client(blob_name)
        if not blob_client.exists():
            logger.warning(f"Blob not found in Azure container: {blob_name}")
            return False
            
        # Ensure parent directories exist
        os.makedirs(os.path.dirname(local_path), exist_ok=True)
        
        with open(local_path, "wb") as file:
            download_stream = blob_client.download_blob()
            file.write(download_stream.readall())
        logger.info(f"Successfully downloaded {blob_name} from Azure Blob to {local_path}")
        return True
    except Exception as e:
        logger.error(f"Error downloading {blob_name} from Azure Blob: {e}")
        return False

def delete_from_blob(blob_name):
    """
    Deletes a file from Azure Blob Storage.
    Returns True if successful, False otherwise.
    """
    client = get_container_client()
    if client is None:
        return False
        
    try:
        blob_client = client.get_blob_client(blob_name)
        if blob_client.exists():
            blob_client.delete_blob()
            logger.info(f"Successfully deleted {blob_name} from Azure Blob.")
            return True
        return False
    except Exception as e:
        logger.error(f"Error deleting {blob_name} from Azure Blob: {e}")
        return False

