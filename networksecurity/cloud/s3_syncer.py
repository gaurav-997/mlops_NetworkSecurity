"""
S3 Syncer for uploading artifacts and models to AWS S3
"""
import os
import sys
from networksecurity.logging.logger import logging
from networksecurity.exception.exception import CustomException


class S3Sync:
    """
    Class to handle syncing of local directories to AWS S3 bucket.
    """
    
    def __init__(self):
        """
        Initialize S3Sync.
        Requires AWS credentials to be configured:
        - AWS_ACCESS_KEY_ID
        - AWS_SECRET_ACCESS_KEY
        - AWS_REGION (optional, defaults to us-east-1)
        """
        try:
            import boto3
            self.s3_client = boto3.client('s3')
            self.s3_resource = boto3.resource('s3')
            logging.info("S3 client initialized successfully")
        except ImportError:
            raise CustomException(
                "boto3 is not installed. Please install: pip install boto3", 
                sys
            )
        except Exception as e:
            raise CustomException(e, sys)
    
    def sync_folder_to_s3(
        self, 
        folder_path: str, 
        bucket_name: str, 
        s3_folder_name: str
    ) -> bool:
        """
        Sync a local folder to S3 bucket.
        
        Args:
            folder_path: Local folder path to sync
            bucket_name: S3 bucket name
            s3_folder_name: S3 folder/prefix name
            
        Returns:
            bool: True if sync successful, False otherwise
        """
        try:
            logging.info(f"Starting sync: {folder_path} -> s3://{bucket_name}/{s3_folder_name}")
            
            if not os.path.exists(folder_path):
                logging.error(f"Local folder does not exist: {folder_path}")
                return False
            
            # Upload all files in the folder
            file_count = 0
            for root, dirs, files in os.walk(folder_path):
                for file in files:
                    local_file_path = os.path.join(root, file)
                    
                    # Calculate relative path for S3
                    relative_path = os.path.relpath(local_file_path, folder_path)
                    s3_key = os.path.join(s3_folder_name, relative_path).replace("\\", "/")
                    
                    # Upload file
                    logging.info(f"Uploading: {local_file_path} -> s3://{bucket_name}/{s3_key}")
                    self.s3_client.upload_file(local_file_path, bucket_name, s3_key)
                    file_count += 1
            
            logging.info(f"Successfully synced {file_count} files to S3")
            return True
            
        except Exception as e:
            logging.error(f"Failed to sync folder to S3: {str(e)}")
            raise CustomException(e, sys)
    
    def sync_folder_from_s3(
        self, 
        folder_path: str, 
        bucket_name: str, 
        s3_folder_name: str
    ) -> bool:
        """
        Sync a S3 folder to local directory.
        
        Args:
            folder_path: Local folder path to download to
            bucket_name: S3 bucket name
            s3_folder_name: S3 folder/prefix name
            
        Returns:
            bool: True if sync successful, False otherwise
        """
        try:
            logging.info(f"Starting sync: s3://{bucket_name}/{s3_folder_name} -> {folder_path}")
            
            # Create local folder if it doesn't exist
            os.makedirs(folder_path, exist_ok=True)
            
            # Download all files from S3 folder
            bucket = self.s3_resource.Bucket(bucket_name)
            file_count = 0
            
            for obj in bucket.objects.filter(Prefix=s3_folder_name):
                # Skip if it's a folder
                if obj.key.endswith('/'):
                    continue
                
                # Calculate local file path
                relative_path = os.path.relpath(obj.key, s3_folder_name)
                local_file_path = os.path.join(folder_path, relative_path)
                
                # Create subdirectories if needed
                os.makedirs(os.path.dirname(local_file_path), exist_ok=True)
                
                # Download file
                logging.info(f"Downloading: s3://{bucket_name}/{obj.key} -> {local_file_path}")
                bucket.download_file(obj.key, local_file_path)
                file_count += 1
            
            logging.info(f"Successfully downloaded {file_count} files from S3")
            return True
            
        except Exception as e:
            logging.error(f"Failed to sync folder from S3: {str(e)}")
            raise CustomException(e, sys)
