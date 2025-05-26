"""
Script to archive old folders in an S3 bucket.

This script moves folders (top-level prefixes) from a specified S3 bucket
to an archive directory within the same bucket if the folder name (assumed
to start with a four-digit year-month representation like '2412' for Dec 2024)
is older than or equal to a specified cutoff date.
"""
import json
# import os # Removed as it's unused
import sys # For sys.exit()
import boto3 # type: ignore
from botocore.exceptions import ClientError # type: ignore

def get_aws_credentials():
    """Load AWS credentials from config file."""
    try:
        # Consider making config.json path configurable or using environment variables
        with open('./../config.json', 'r', encoding='utf-8') as f:
            config = json.load(f)
            return config['aws_access_key_id'], config['aws_secret_access_key']
    except FileNotFoundError as exc:
        raise RuntimeError("config.json not found. Please create it with AWS credentials.") from exc
    except KeyError as exc:
        raise RuntimeError("AWS credentials not found in config.json.") from exc

def check_bucket_exists(s3_client, bucket_name):
    """Check if S3 bucket exists and is accessible."""
    try:
        s3_client.head_bucket(Bucket=bucket_name)
        return True
    except ClientError as e:
        error_code = int(e.response['Error']['Code'])
        if error_code == 403:
            # Re-raise with the original exception for context
            raise RuntimeError(f"Access denied to bucket: {bucket_name}") from e
        if error_code == 404:
            raise RuntimeError(f"Bucket does not exist: {bucket_name}") from e
        # For other ClientErrors, raise a more generic error but include original
        raise RuntimeError(f"Error accessing bucket {bucket_name}: {e}") from e
    return False # Should not be reached if exception is raised

# pylint: disable=too-many-locals, too-many-nested-blocks
def move_folders_to_archive(source_bucket, archive_prefix="snake-venom-binder",
                            cutoff_date="2412"):
    """
    Move folders to an archive directory within the same S3 bucket.

    Folders are identified by top-level prefixes. A folder is moved if its
    name (e.g., '2412_some_name') starts with a date string (YYMM) that is
    less than or equal to the cutoff_date.
    """
    aws_access_key_id, aws_secret_access_key = get_aws_credentials()

    s3_client = boto3.client('s3',
                             aws_access_key_id=aws_access_key_id,
                             aws_secret_access_key=aws_secret_access_key)

    check_bucket_exists(s3_client, source_bucket)

    paginator = s3_client.get_paginator('list_objects_v2')
    processed_folders = set()
    moved_count = 0

    for page in paginator.paginate(Bucket=source_bucket, Delimiter='/'):
        # Process common prefixes (folders)
        for common_prefix in page.get('CommonPrefixes', []):
            folder = common_prefix.get('Prefix').strip('/') # Get folder name

            if folder in processed_folders or folder == archive_prefix:
                continue

            try:
                # Assuming folder name starts with YYMM format e.g., "2412"
                folder_date_str = folder[:4]
                if not folder_date_str.isdigit() or len(folder_date_str) != 4:
                    print(f"Skipping folder with non-date prefix: {folder}")
                    continue
                folder_date = int(folder_date_str)

                if folder_date <= int(cutoff_date):
                    print(f"Preparing to move folder: {folder}")

                    # List all objects in this folder
                    folder_objects_paginator = s3_client.get_paginator('list_objects_v2')
                    for objects_page in folder_objects_paginator.paginate(
                        Bucket=source_bucket, Prefix=f"{folder}/"
                    ):
                        for s3_object in objects_page.get('Contents', []):
                            try:
                                old_key = s3_object['Key']
                                new_key = f"{archive_prefix}/{old_key}"

                                print(f"  Copying {old_key} to {new_key}")
                                s3_client.copy_object(
                                    CopySource={'Bucket': source_bucket, 'Key': old_key},
                                    Bucket=source_bucket,
                                    Key=new_key
                                )

                                print(f"  Deleting {old_key}")
                                s3_client.delete_object(
                                    Bucket=source_bucket,
                                    Key=old_key
                                )
                            except ClientError as e_obj:
                                print(f"  Error processing object {old_key}: {e_obj}")
                                # Decide if we should stop or continue with other objects
                                continue # Continue with the next object in the folder
                        # After processing all objects in the folder
                        processed_folders.add(folder)
                        moved_count += 1
                        print(f"Successfully moved contents of folder {folder} "
                              f"to {archive_prefix}/{folder}")

            except ValueError: # Handles int(cutoff_date) or int(folder_date_str) failure
                print(f"Skipping folder with invalid date format: {folder}")
            except ClientError as e_folder: # Catch errors during folder processing (e.g. list_objects)
                print(f"ClientError while processing folder {folder}: {e_folder}")
            except Exception as e_unexpected: # Catch any other unexpected error
                err_type = type(e_unexpected).__name__
                print(f"Unexpected error processing folder {folder}:")
                print(f"  Type: {err_type}, Error: {e_unexpected}")
                # Potentially add 'continue' if you want to proceed with other folders

    return moved_count

if __name__ == "__main__":
    SOURCE_BUCKET_NAME = "bindcraft"
    ARCHIVE_PREFIX_PATH = "snake-venom-binder" # Clarified name
    CUTOFF_DATE_STR = "2502" # Clarified name

    try:
        moved_folders_count = move_folders_to_archive(
            SOURCE_BUCKET_NAME,
            ARCHIVE_PREFIX_PATH,
            CUTOFF_DATE_STR
        )
        print(f"Archive process completed. Moved {moved_folders_count} "
              "folders' contents.")
    except RuntimeError as e: # Catching specific RuntimeError from helper functions
        print(f"Error during script execution: {e}")
        sys.exit(1)
    except ClientError as e: # Catch Boto3 client errors not caught by helpers
        print(f"AWS Client Error during archiving process: {e}")
        sys.exit(1)
    except Exception as e: # General catch for other unexpected errors
        print(f"An unexpected error occurred: {type(e).__name__} - {e}")
        sys.exit(1)
