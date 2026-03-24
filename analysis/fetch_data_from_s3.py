import marimo

__generated_with = "0.20.4"
app = marimo.App()


@app.cell
def _():
    import json 
    import boto3

    return boto3, json


@app.cell
def _(json):
    config_data = json.load(open('./../config.json'))
    aws_access_key_id = config_data['aws_access_key_id']
    aws_secret_access_key = config_data['aws_secret_access_key']
    config_data.keys()
    return aws_access_key_id, aws_secret_access_key


@app.cell
def _(aws_access_key_id, aws_secret_access_key, boto3):
    # create a s3 client
    s3_client = boto3.client('s3', aws_access_key_id=aws_access_key_id, aws_secret_access_key=aws_secret_access_key)
    return


@app.cell
def _(boto3):
    def list_s3_folders(bucket_name):
        s3_client = boto3.client('s3')
        paginator = s3_client.get_paginator('list_objects_v2')
        pages = paginator.paginate(Bucket=_bucket_name)
        folders = set()
        for page in pages:
            if 'Contents' in page:
                for obj in page['Contents']:
                    key = obj['Key']
                    folder = key.split('/')[0]
                    folders.add(folder)
        return sorted(folders)
    _bucket_name = 'bindcraft'
    folders = list_s3_folders(_bucket_name)
    print('Folders in S3 bucket:')
    for folder in folders:
        print(folder)
    return


@app.cell
def _(boto3):
    import os

    def download_s3_folder(bucket_name, s3_folder, local_dir):
        s3_client = boto3.client('s3')
        if not os.path.exists(local_dir):
            os.makedirs(local_dir)
        paginator = s3_client.get_paginator('list_objects_v2')
        pages = paginator.paginate(Bucket=_bucket_name, Prefix=s3_folder)
        for page in pages:
            if 'Contents' in page:
                for obj in page['Contents']:
                    s3_key = obj['Key']
                    local_file_path = os.path.join(local_dir, os.path.relpath(s3_key, s3_folder))
                    local_file_dir = os.path.dirname(local_file_path)
                    if not os.path.exists(local_file_dir):
                        os.makedirs(local_file_dir)
                    s3_client.download_file(_bucket_name, s3_key, local_file_path)
                    print(f'Downloaded {s3_key} to {local_file_path}')
    _bucket_name = 'bindcraft'
    s3_folder = '2502152323'
    local_dir = f'./out/bindcraft/{s3_folder}'
    download_s3_folder(_bucket_name, s3_folder, local_dir)
    return


@app.cell
def _(boto3):
    # 1. Get S3 folders
    def get_s3_folders(bucket_name, aws_access_key_id, aws_secret_access_key, prefix='snake-venom-binder/'):
        """
        Retrieves a list of top-level folder names from a specified S3 path.
        """
        s3_client = boto3.client('s3', aws_access_key_id=aws_access_key_id, aws_secret_access_key=aws_secret_access_key)
        paginator = s3_client.get_paginator('list_objects_v2')
        folders = set()
        for page in paginator.paginate(Bucket=_bucket_name, Prefix=prefix, Delimiter='/'):
            for common_prefix in page.get('CommonPrefixes', []):
                folder_path = common_prefix.get('Prefix')
                if folder_path.startswith(prefix):
                    folder_name = folder_path[len(prefix):].split('/')[0]
                    if folder_name:
                        folders.add(folder_name)
        return sorted(list(folders))  # Extract folder name after the main prefix  # Ensure it's not an empty string

    return (get_s3_folders,)


@app.cell
def _(get_s3_folders, json):
    try:
        with open('./../config.json', 'r', encoding='utf-8') as f:
            config = json.load(f)
    except FileNotFoundError:
        print('Error: config.json not found. Please create it with AWS credentials.')
    except json.JSONDecodeError:
        print('Error: config.json is not a valid JSON file.')
    aws_access_key_id_1 = config.get('aws_access_key_id')
    aws_secret_access_key_1 = config.get('aws_secret_access_key')
    _bucket_name = 'bindcraft'
    s3_prefix = 'snake-venom-binder/'
    local_base_download_dir = './../out/bindcraft/snake-venom-binder'
    s3_folders = get_s3_folders(_bucket_name, aws_access_key_id_1, aws_secret_access_key_1, prefix=s3_prefix)
    print(s3_folders)
    return


if __name__ == "__main__":
    app.run()

