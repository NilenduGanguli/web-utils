from fastapi import FastAPI, File, UploadFile, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse,StreamingResponse
from typing import Dict
import os
import io
from typing import List
import json
import shutil
import tempfile
import boto3
from pydantic import BaseModel
from datetime import datetime


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

# class FileMetadata(BaseModel):
#     size: str
#     file_type: str
#     date_modified: str
#     alias: str

# class FilesData(BaseModel):
#     metadata: FileMetadata

# class Files(BaseModel):
#     files: Dict[str, FilesData]

def upload_directory_to_s3(directory_path, s3_url, s3_bucketname, access_key_id, secret_access_key):
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
def fetch_object(s3_url, s3_bucketname, access_key_id, secret_access_key, object_name, destination_file):
    s3 = boto3.client('s3',
                    endpoint_url=s3_url,
                    aws_access_key_id=access_key_id,
                    aws_secret_access_key=secret_access_key)
    try:
        s3.download_file(s3_bucketname, object_name, destination_file)
        print(f"Object {object_name} fetched to {destination_file}")
    except Exception as e:
        print(f"Error fetching object: {e}")

def check_bucket(s3_url, s3_bucketname, access_key_id, secret_access_key):
    s3 = boto3.client('s3',
                      endpoint_url=s3_url,
                      aws_access_key_id=access_key_id,
                      aws_secret_access_key=secret_access_key)

    # Check if the bucket exists
    try:
        s3.head_bucket(Bucket=s3_bucketname)
        return True
    except s3.exceptions.ClientError as e:
        error_code = e.response['Error']['Code']
        if error_code == '404':
            return False
        else:
            # Other error, handle as needed
            print("Error occurred: ", e)
            return False

def list_buckets(s3_url, s3_bucketname, access_key_id, secret_access_key):
    # Initialize a session using MinIO S3 credentials
    s3 = boto3.client('s3',
                      endpoint_url=s3_url,
                      aws_access_key_id=access_key_id,
                      aws_secret_access_key=secret_access_key,
                      )
    bucketList = {}
    # Walk through the directory and upload files to S3
    try:
        objects = s3.list_objects_v2(Bucket=s3_bucketname)
        if 'Contents' in objects:
            for obj in objects['Contents']:
                key = obj['Key']
                obj_info = {
                    'filesize': str(int(obj['Size']/1024)),  # File size in bytes
                    'file_type': key.split('.')[-1],  # File type
                    'date_modified': obj['LastModified'].strftime('%Y-%m-%d %H:%M:%S')  # Date modified
                }
                bucketList[key] = obj_info
        else:
            print("Bucket is empty.")
    except Exception as e:
        print(f"Error listing objects: {e}")
    finally:
        return bucketList

@app.get("/upload_files_local")
async def browse_files_local():
    file_path = "./templates/save_to_s3.html"
    return FileResponse(file_path,media_type="text/html")

@app.get("/upload_files_documentum/index")
async def browse_files_local():
    file_path = "./templates/bucket_browser.html"
    return FileResponse(file_path,media_type="text/html")

@app.get("/upload_files_documentum/bucket_browser")
async def browse_files_local(bucket_name : str):
    if not check_bucket(s3_url,bucket_name,access_key_id,secret_access_key):
        return f"Bucket Not Available at {s3_url}"
    else :
        file_path = "./templates/bucket_viewer.html"
        bucketlist = list_buckets(s3_url,bucket_name,access_key_id,secret_access_key)
        if 'metadata.json' in bucketlist:
            temp_dir = tempfile.mkdtemp()
            try:
                temp_file_path = os.path.join(temp_dir, "metadata.json")
                print(temp_file_path)
                fetch_object(s3_url,bucket_name,access_key_id,secret_access_key,'metadata.json',temp_file_path)
                with open(temp_file_path) as infile: 
                    metadata =json.loads(infile.read())
                    for item in bucketlist:
                        if item in metadata:
                            bucketlist[item].update({'alias':metadata[item]})
                for item in bucketlist:
                    wrapper = bucketlist[item]
                    bucketlist[item] = {'metadata':wrapper}
            finally :
                shutil.rmtree(temp_dir)
            mid_data = str(bucketlist)
            part1 = ""
            part2 = ""
            with open("./templates/bucket_viewer_part1.html","r") as infile:
                part1 = infile.read()
            with open("./templates/bucket_viewer_part2.html","r") as infile:
                part2 = infile.read()
            return_string = part1 + mid_data + part2
            return_file = io.BytesIO(return_string.encode("utf-8"))
            # StreamingResponse(iter([return_file.getvalue()]), media_type="text/html")
        return StreamingResponse(iter([return_file.getvalue()]), media_type="text/html")
    
@app.post("/upload_files_documentum/send")
async def get_selected_files(selected_json : str = Form(...)):
    print(selected_json)


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
