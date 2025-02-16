import boto3
import json
from datetime import datetime
from botocore.exceptions import ClientError

def get_aws_credentials():
    """Load AWS credentials from config file"""
    try:
        with open('./../config.json') as f:
            config = json.load(f)
            return config['aws_access_key_id'], config['aws_secret_access_key']
    except FileNotFoundError:
        raise Exception("config.json not found. Please create it with AWS credentials.")
    except KeyError:
        raise Exception("AWS credentials not found in config.json")

def check_bucket_exists(s3_client, bucket_name):
    """Check if S3 bucket exists and is accessible"""
    try:
        s3_client.head_bucket(Bucket=bucket_name)
        return True
    except ClientError as e:
        error_code = int(e.response['Error']['Code'])
        if error_code == 403:
            raise Exception(f"Access denied to bucket: {bucket_name}")
        elif error_code == 404:
            raise Exception(f"Bucket does not exist: {bucket_name}")
        else:
            raise Exception(f"Error accessing bucket {bucket_name}: {str(e)}")

def move_folders_to_archive(source_bucket, archive_prefix="snake-venom-binder", cutoff_date="2412"):
    """Move folders to archive directory within the same bucket"""
    
    # Get AWS credentials
    aws_access_key_id, aws_secret_access_key = get_aws_credentials()
    
    # Initialize S3 client
    s3_client = boto3.client('s3',
                            aws_access_key_id=aws_access_key_id,
                            aws_secret_access_key=aws_secret_access_key)
    
    # Verify bucket exists
    check_bucket_exists(s3_client, source_bucket)
    
    paginator = s3_client.get_paginator('list_objects_v2')
    processed_folders = set()
    moved_count = 0

    for page in paginator.paginate(Bucket=source_bucket):
        if 'Contents' in page:
            for obj in page['Contents']:
                folder = obj['Key'].split('/')[0]
                
                if folder in processed_folders or folder == archive_prefix:
                    continue
                
                try:
                    folder_date = int(folder[:4])
                    if folder_date <= int(cutoff_date):
                        print(f"Moving folder: {folder}")
                        
                        # Get all objects in this folder
                        folder_objects = s3_client.list_objects_v2(
                            Bucket=source_bucket,
                            Prefix=f"{folder}/"
                        )
                        
                        for folder_obj in folder_objects.get('Contents', []):
                            try:
                                old_key = folder_obj['Key']
                                new_key = f"{archive_prefix}/{old_key}"
                                
                                # Copy to archive folder
                                s3_client.copy_object(
                                    CopySource={'Bucket': source_bucket, 'Key': old_key},
                                    Bucket=source_bucket,
                                    Key=new_key
                                )
                                
                                # Delete original after successful copy
                                s3_client.delete_object(
                                    Bucket=source_bucket,
                                    Key=old_key
                                )
                            except ClientError as e:
                                print(f"Error processing object {old_key}: {str(e)}")
                                continue
                        
                        processed_folders.add(folder)
                        moved_count += 1
                        print(f"Successfully moved folder {folder} to archive directory")
                
                except (ValueError, IndexError):
                    print(f"Skipping folder with invalid date format: {folder}")
                    continue
    
    return moved_count

if __name__ == "__main__":
    SOURCE_BUCKET = "bindcraft"
    ARCHIVE_PREFIX = "snake-venom-binder"
    CUTOFF_DATE = "2502"
    
    try:
        moved_folders = move_folders_to_archive(SOURCE_BUCKET, ARCHIVE_PREFIX, CUTOFF_DATE)
        print(f"Archive process completed successfully. Moved {moved_folders} folders.")
    except Exception as e:
        print(f"Error during archiving process: {str(e)}")
        exit(1)