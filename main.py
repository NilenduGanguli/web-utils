from fastapi import FastAPI, File, UploadFile, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import os
from typing import List
import json
import shutil
import tempfile
import boto3

s3_url = "http://localhost:9000"
s3_bucketname = "test1"
access_key_id = "accesskey"
secret_access_key = "secretkey"

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
def upload_directory_to_s3(directory_path, s3_url, s3_bucketname, access_key_id, secret_access_key):
    # Initialize a session using MinIO S3 credentials
    s3 = boto3.client('s3',
                      endpoint_url=s3_url,
                      aws_access_key_id=access_key_id,
                      aws_secret_access_key=secret_access_key,
                      )

    # Walk through the directory and upload files to S3
    for root, dirs, files in os.walk(directory_path):
        for file in files:
            file_path = os.path.join(root, file)
            s3_object_key = os.path.relpath(file_path, directory_path)

            # Upload the file to S3
            try:
                s3.upload_file(file_path, s3_bucketname, s3_object_key)
                print(f"Uploaded {file_path} to {s3_bucketname}/{s3_object_key}")
            except Exception as e:
                print(f"Failed to upload {file_path}: {e}")
@app.post("/upload")
async def upload_files(files: List[UploadFile] = File(...), metadata: str = Form(...)):
    # Create a dictionary from the JSON string metadata
    metadata_dict = json.loads(metadata)

    # Create a temporary directory to store the files
    with tempfile.TemporaryDirectory() as temp_dir:
        print(temp_dir)
        for file in files:
            # Save each file to the temporary directory
            file_path = os.path.join(temp_dir, file.filename)
            with open(file_path, "wb") as buffer:
                shutil.copyfileobj(file.file, buffer)

            # Write metadata to a JSON file with the same name as the uploaded file
        metadata_file_path = os.path.join(temp_dir,"metadata.json")
        with open(metadata_file_path, "w") as metadata_file:
            json.dump(metadata_dict, metadata_file)

        # You can process the files further if needed, outside the 'with' block.
        if len(os.listdir(temp_dir)) >0:
            upload_directory_to_s3(temp_dir,s3_url,s3_bucketname,access_key_id,secret_access_key)

    return {"message": "Files uploaded successfully"}
