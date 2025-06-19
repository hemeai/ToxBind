"""
This script automates the processing of new data folders from S3.
It performs the following steps:
1. Lists folders in a specified S3 bucket and prefix.
2. Compares this list with a list of already processed folders (from 'final_results.csv').
3. Downloads any new, unprocessed folders from S3 to a local directory.
4. Runs a series of analysis scripts (combine_outputs.py, get_ipae_score.py,
   result_analysis.py) on the data in each newly downloaded folder.
"""
import json
import os
import subprocess
import boto3 # type: ignore
import pandas as pd # type: ignore


# 1. Get S3 folders
def get_s3_folders(bucket_name, aws_access_key_id, aws_secret_access_key,
                   prefix='snake-venom-binder/'):
    """
    Retrieves a list of top-level folder names from a specified S3 path.
    """
    s3_client = boto3.client('s3',
                             aws_access_key_id=aws_access_key_id,
                             aws_secret_access_key=aws_secret_access_key)

    paginator = s3_client.get_paginator('list_objects_v2')
    folders = set()

    for page in paginator.paginate(Bucket=bucket_name, Prefix=prefix, Delimiter='/'):
        for common_prefix in page.get('CommonPrefixes', []):
            # Extract folder name after the main prefix
            folder_path = common_prefix.get('Prefix')
            if folder_path.startswith(prefix):
                folder_name = folder_path[len(prefix):].split('/')[0]
                if folder_name: # Ensure it's not an empty string
                    folders.add(folder_name)
    return sorted(list(folders))

# 2. Get processed folders from final_results.csv
def get_processed_folders():
    """
    Reads 'final_results.csv' and returns a set of processed folder names.
    Returns an empty set if the file is not found.
    """
    try:
        df = pd.read_csv('final_results.csv')
        return set(df['Folder'].astype(str).unique())
    except FileNotFoundError:
        return set()

# 3. Download new folders from S3
def download_s3_folder(bucket_name, s3_folder_prefix, local_dir_base, s3_client):
    """
    Downloads all objects from a specific S3 folder prefix to a local directory.
    """
    # s3_folder_prefix should be the full path like "snake-venom-binder/folder_name/"
    local_folder_path = os.path.join(local_dir_base, os.path.basename(s3_folder_prefix.strip('/')))
    if not os.path.exists(local_folder_path):
        os.makedirs(local_folder_path)

    paginator = s3_client.get_paginator('list_objects_v2')
    for page in paginator.paginate(Bucket=bucket_name, Prefix=s3_folder_prefix):
        for obj in page.get('Contents', []):
            s3_key = obj['Key']
            # Ensure local_file_path is relative to the specific folder being downloaded
            relative_path = os.path.relpath(s3_key, s3_folder_prefix)
            local_file_path = os.path.join(local_folder_path, relative_path)

            # Ensure directory for the file exists
            local_file_dir = os.path.dirname(local_file_path)
            if not os.path.exists(local_file_dir):
                os.makedirs(local_file_dir, exist_ok=True)

            # Avoid trying to download directory markers if they appear as objects
            if not s3_key.endswith('/'):
                print(f"Downloading {s3_key} to {local_file_path}")
                s3_client.download_file(bucket_name, s3_key, local_file_path)


def check_local_folder(folder_name, base_path='./../out/bindcraft/snake-venom-binder'):
    """Check if folder exists locally."""
    folder_path = os.path.join(base_path, folder_name)
    return os.path.exists(folder_path)

# Main workflow
def main(): # pylint: disable=too-many-locals
    """
    Main workflow to identify, download, and process new S3 folders.
    """
    # Load AWS credentials
    try:
        with open('./../config.json', 'r', encoding='utf-8') as f:
            config = json.load(f)
    except FileNotFoundError:
        print("Error: config.json not found. Please create it with AWS credentials.")
        return
    except json.JSONDecodeError:
        print("Error: config.json is not a valid JSON file.")
        return

    aws_access_key_id = config.get('aws_access_key_id')
    aws_secret_access_key = config.get('aws_secret_access_key')

    if not aws_access_key_id or not aws_secret_access_key:
        print("Error: AWS credentials not found or incomplete in config.json.")
        return

    bucket_name = 'bindcraft'
    s3_prefix = 'snake-venom-binder/' # Corrected variable name for clarity
    local_base_download_dir = './../out/bindcraft/snake-venom-binder'

    # Get all S3 folders with prefix
    s3_folders = get_s3_folders(bucket_name, aws_access_key_id, aws_secret_access_key, prefix=s3_prefix)

    processed_folders = get_processed_folders()
    new_folders = set(s3_folders) - processed_folders

    if not new_folders:
        print("No new folders to process.")
        return 
    else:
        print(f"Found {len(new_folders)} new folder(s) to process: {new_folders}")


    # if not new_folders:
    #     print("No new folders to process.")
    #     return

    s3_client = boto3.client('s3',
                             aws_access_key_id=aws_access_key_id,
                             aws_secret_access_key=aws_secret_access_key)

    for folder_name in new_folders:
        print(f"Processing folder: {folder_name}")

        if check_local_folder(folder_name, base_path=local_base_download_dir):
            print(f"Folder {folder_name} exists locally, skipping download.")
        else:
            # Construct the full S3 prefix for the folder to download
            full_s3_folder_prefix = f"{s3_prefix}{folder_name}/"
            download_s3_folder(bucket_name, full_s3_folder_prefix,
                               local_base_download_dir, s3_client)

        # Run the analysis pipeline
        analysis_scripts = ['combine_outputs.py', 'get_ipae_score.py', 'result_analysis.py']
        for script_name in analysis_scripts:
            try:
                print(f"Running {script_name} for folder {folder_name}...")
                # Note: These scripts might need to be aware of the specific folder context.
                # Currently, they seem to operate on fixed file names like 'combined_data.csv'.
                # This might require the scripts to be run from a specific working directory
                # or be modified to accept the folder path as an argument.
                # For now, assuming they are run in a context where they find their inputs.
                subprocess.run(['python', script_name], check=True, text=True)
                print(f"Successfully ran {script_name} for folder {folder_name}.")
            except subprocess.CalledProcessError as e:
                print(f"Error running {script_name} for folder {folder_name}: {e}")
                # Decide if we should stop processing this folder or continue
                break # Stop processing this folder if one script fails
            except FileNotFoundError:
                print(f"Error: Script {script_name} not found.")
                break # Stop processing this folder

if __name__ == "__main__":
    main()