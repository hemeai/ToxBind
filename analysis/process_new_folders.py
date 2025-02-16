import json
import boto3
import pandas as pd
import subprocess
import os

# 1. Get S3 folders
def get_s3_folders(bucket_name, aws_access_key_id, aws_secret_access_key, prefix='snake-venom-binder/'):
    s3_client = boto3.client('s3', 
                            aws_access_key_id=aws_access_key_id,
                            aws_secret_access_key=aws_secret_access_key)
    
    paginator = s3_client.get_paginator('list_objects_v2')
    folders = set()
    
    for page in paginator.paginate(Bucket=bucket_name, Prefix=prefix):
        if 'Contents' in page:
            for obj in page['Contents']:
                # Extract folder name after prefix
                path = obj['Key'][len(prefix):] if obj['Key'].startswith(prefix) else obj['Key']
                folder = path.split('/')[0]
                if folder:
                    folders.add(folder)
    
    return sorted(folders)

# 2. Get processed folders from final_results.csv
def get_processed_folders():
    try:
        df = pd.read_csv('final_results.csv')
        return set(df['Folder'].unique())
    except FileNotFoundError:
        return set()

# 3. Download new folders from S3
def download_s3_folder(bucket_name, s3_folder, local_dir, s3_client):
    if not os.path.exists(local_dir):
        os.makedirs(local_dir)
    
    paginator = s3_client.get_paginator('list_objects_v2')
    pages = paginator.paginate(Bucket=bucket_name, Prefix=s3_folder)
    
    for page in pages:
        if 'Contents' in page:
            for obj in page['Contents']:
                s3_key = obj['Key']
                local_file_path = os.path.join(local_dir, os.path.relpath(s3_key, s3_folder))
                os.makedirs(os.path.dirname(local_file_path), exist_ok=True)
                s3_client.download_file(bucket_name, s3_key, local_file_path)


def check_local_folder(folder, base_path='./../out/bindcraft/snake-venom-binder'):
    """Check if folder exists locally with required files"""
    folder_path = os.path.join(base_path, folder)
    return os.path.exists(folder_path)

# Main workflow
def main():
    # Load AWS credentials
    with open('./../config.json') as f:
        config = json.load(f)
    
    aws_access_key_id = config['aws_access_key_id']
    aws_secret_access_key = config['aws_secret_access_key']
    
    # Fix: Separate bucket name and prefix
    bucket_name = 'bindcraft'
    prefix = 'snake-venom-binder/'

    # Get all S3 folders with prefix
    s3_folders = get_s3_folders(bucket_name, aws_access_key_id, aws_secret_access_key)
    
    # Get processed folders
    processed_folders = get_processed_folders()
    
    # Find new folders to process
    new_folders = set(s3_folders) - processed_folders
    
    if not new_folders:
        print("No new folders to process")
        return

    # Create S3 client
    s3_client = boto3.client('s3', 
                            aws_access_key_id=aws_access_key_id,
                            aws_secret_access_key=aws_secret_access_key)

    # Process each new folder
    for folder in new_folders:
        print(f"Processing folder: {folder}")
        
        # Check if folder exists locally
        if check_local_folder(folder):
            print(f"Folder {folder} exists locally, skipping download")
        else:
            # Download only if not present locally
            local_dir = os.path.join('./../out/bindcraft/snake-venom-binder', folder)
            folder_path = f"{prefix}{folder}"
            download_s3_folder(bucket_name, folder_path, local_dir, s3_client)
        
        # Run the analysis pipeline
        try:
            # Run analysis scripts
            subprocess.run(['python', 'combine_outputs.py'])
            subprocess.run(['python', 'get_ipae_score.py'])
            subprocess.run(['python', 'result_analysis.py'])
            print(f"Successfully processed folder: {folder}")
        except Exception as e:
            print(f"Error processing folder {folder}: {str(e)}")

if __name__ == "__main__":
    main()