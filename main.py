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
s3_bucketname_global = "test1"
access_key_id = "accesskey"
secret_access_key = "secretkey"
strict_bucket = True

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
def bucket_entitlement(soeid : str, bucket_name : str):
    if soeid in bucket_name :
        return None
    else :
        return {"entitlement" : "!! service under development !!"}
def upload_directory_to_s3(directory_path, s3_url, s3_bucketname, access_key_id, secret_access_key):
    s3 = boto3.client('s3',
                      endpoint_url=s3_url,
                      aws_access_key_id=access_key_id,
                      aws_secret_access_key=secret_access_key,
                      )
    if strict_bucket : 
        bucket_name = s3_bucketname_global
        prefix = s3_bucketname
    else :
        if '/' in s3_bucketname:
            bucket_name, prefix = s3_bucketname.split('/', 1)
        else:
            bucket_name = s3_bucketname
            prefix = ''
    print("bucket_name : " + bucket_name)
    print("sub_path : " + prefix)
    for root, dirs, files in os.walk(directory_path):
        for file in files:
            file_path = os.path.join(root, file)
            s3_object_key = prefix + "/" + os.path.relpath(file_path, directory_path)
            # Upload the file to S3
            try:
                s3.upload_file(file_path, bucket_name, s3_object_key)
                print(f"Uploaded {file_path} to {bucket_name}/{s3_object_key}")
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
#old version
# def check_bucket(s3_url, s3_bucketname, access_key_id, secret_access_key):
#     s3 = boto3.client('s3',
#                       endpoint_url=s3_url,
#                       aws_access_key_id=access_key_id,
#                       aws_secret_access_key=secret_access_key)

#     try:
#         s3.head_bucket(Bucket=s3_bucketname)
#         return True
#     except s3.exceptions.ClientError as e:
#         error_code = e.response['Error']['Code']
#         if error_code == '404':
#             return False
#         else:
#             print("Error occurred: ", e)
#             return False
def check_bucket(s3_url, bucket_or_path, access_key_id, secret_access_key):
    s3 = boto3.client('s3',
                      endpoint_url=s3_url,
                      aws_access_key_id=access_key_id,
                      aws_secret_access_key=secret_access_key)
    
    try:
        if '/' in bucket_or_path:
            bucket_name, prefix = bucket_or_path.split('/', 1)
        else:
            bucket_name = bucket_or_path
            prefix = ''
        print("bucket_name : " + bucket_name)
        print("sub_path : " + prefix)
        s3.head_bucket(Bucket=bucket_name)
        response = s3.list_objects_v2(Bucket=bucket_name, Prefix=prefix, MaxKeys=1)
        if 'Contents' in response:
            print("Check Bucket : " + bucket_or_path + " Success ")
            return True
        else:
            return False
        
    except s3.exceptions.ClientError as e:
        error_code = e.response['Error']['Code']
        if error_code == '404':
            # Bucket not found
            return False
        else:
            print("Error occurred: ", e)
            return False
#old version
# def list_buckets(s3_url, s3_bucketname, access_key_id, secret_access_key):
#     s3 = boto3.client('s3',
#                       endpoint_url=s3_url,
#                       aws_access_key_id=access_key_id,
#                       aws_secret_access_key=secret_access_key,
#                       )
#     bucketList = {}
#     try:
#         objects = s3.list_objects_v2(Bucket=s3_bucketname)
#         if 'Contents' in objects:
#             for obj in objects['Contents']:
#                 key = obj['Key']
#                 obj_info = {
#                     'filesize': str(int(obj['Size']/1024)),  # File size in bytes
#                     'file_type': key.split('.')[-1],  # File type
#                     'date_modified': obj['LastModified'].strftime('%Y-%m-%d %H:%M:%S')  # Date modified
#                 }
#                 bucketList[key] = obj_info
#         else:
#             print("Bucket is empty.")
#     except Exception as e:
#         print(f"Error listing objects: {e}")
#     finally:
#         return bucketList
def list_buckets(s3_url, bucket_or_folder_name, access_key_id, secret_access_key):
    s3 = boto3.client('s3',
                      endpoint_url=s3_url,
                      aws_access_key_id=access_key_id,
                      aws_secret_access_key=secret_access_key,
                      )
    
    bucket_list = {}
    if '/' in bucket_or_folder_name:
        bucket_name, prefix = bucket_or_folder_name.split('/', 1)
    else:
        bucket_name = bucket_or_folder_name
        prefix = ''
    # Using paginator to handle a large number of objects
    paginator = s3.get_paginator('list_objects_v2')
    try:
        for page in paginator.paginate(Bucket=bucket_name, Prefix=prefix):
            if 'Contents' in page:
                for obj in page['Contents']:
                    key = obj['Key']
                    obj_info = {
                        'filesize': str(int(obj['Size'] / 1024)),  # File size in kilobytes
                        'file_type': key.split('.')[-1],  # File type
                        'date_modified': obj['LastModified'].strftime('%Y-%m-%d %H:%M:%S')  # Date modified
                    }
                    bucket_list[key] = obj_info
            else:
                print("No contents found in the specified bucket or folder.")
    except Exception as e:
        print(f"Error listing objects: {e}")
    
    return bucket_list

@app.get("/upload_files_local")
async def browse_files_local():
    file_path = "./templates/save_to_s3.html"
    return FileResponse(file_path,media_type="text/html")

@app.get("/upload_files_documentum/index")
async def browse_files_local():
    file_path = "./templates/bucket_browser.html"
    return FileResponse(file_path,media_type="text/html")

# document category
# document subcategory
# description

# check_entitlement returns null => check only his folder

# enlarge document preview
@app.get("/upload_files_documentum/bucket_browser")
async def browse_files_local(bucket_name : str, soeid : str):
    part1 = ""
    part2 = ""
    mid_data = "Error in Accessing or Parsing Bucket Contents!!"
    if strict_bucket :
        bucket_name = s3_bucketname_global+"/"+bucket_name
    if bucket_entitlement(soeid,bucket_name) :
        return f"Entitlements : {str(bucket_entitlement(soeid,bucket_name))}"
    print("!!!"+bucket_name)
    if not check_bucket(s3_url,bucket_name,access_key_id,secret_access_key):
        return f"Bucket Not Available at {s3_url}"
    else :
        bucketlist = list_buckets(s3_url,bucket_name,access_key_id,secret_access_key)
        metadata_file_name = "/".join([*bucket_name.split("/")[1:],'metadata.json'])
        print(metadata_file_name)
        if metadata_file_name in bucketlist:
            print("Metadata file found at : "+bucket_name)
            temp_dir = tempfile.mkdtemp()
            try:
                temp_file_path = os.path.join(temp_dir, "metadata.json")
                print("Saving Metadata to : "+temp_file_path)
                if '/' in bucket_name:
                    bucket_name, _ = bucket_name.split('/', 1)
                fetch_object(s3_url,bucket_name,access_key_id,secret_access_key,metadata_file_name,temp_file_path)
                with open(temp_file_path) as infile: 
                    metadata =json.loads(infile.read())
                    for item in bucketlist:
                        if item.split("/")[-1] in metadata:
                            sub_dict = metadata[item.split("/")[-1]]
                            if isinstance(sub_dict,dict):
                                bucketlist[item].update({'document_category':sub_dict["document_category"],'document_subcategory':sub_dict['document_subcategory'],'description':sub_dict['document_description']})
                            else : 
                                bucketlist[item].update({'alias':metadata[item.split("/")[-1]]})
                for item in bucketlist:
                    wrapper = bucketlist[item]
                    bucketlist[item] = {'metadata':wrapper}
            finally :
                shutil.rmtree(temp_dir)
            mid_data = str(bucketlist)
            with open("./templates/bucket_viewer_part1.html","r") as infile:
                part1 = infile.read()
            with open("./templates/bucket_viewer_part2.html","r") as infile:
                part2 = infile.read()
        else :
            print("Metadata file NOT found at : "+bucket_name)
        return_string = part1 + mid_data + part2
        return_file = io.BytesIO(return_string.encode("utf-8"))
        # StreamingResponse(iter([return_file.getvalue()]), media_type="text/html")
        return StreamingResponse(iter([return_file.getvalue()]), media_type="text/html")
    
@app.post("/upload_files_documentum/send")
async def get_selected_files(selected_json : str = Form(...)):
    print(selected_json)


@app.post("/upload")
async def upload_files(files: List[UploadFile] = File(...), metadata: str = Form(...), bucket_name : str = Form(...), soeid : str = Form(...)):
    if strict_bucket :
        bucket_name = s3_bucketname_global+"/"+bucket_name
    if bucket_entitlement(soeid,bucket_name) :
        return f"Entitlements : {str(bucket_entitlement(soeid,bucket_name))}"
    metadata_dict = json.loads(metadata)
    print("Using Bucket : "+str(bucket_name))
    if '/' in bucket_name:
        bucket_name_trunc, _ = bucket_name.split('/', 1)
    else :
        bucket_name_trunc = bucket_name
    if not check_bucket(s3_url,bucket_name_trunc,access_key_id,secret_access_key):
        return f"Bucket Not Available at {s3_url}"
    with tempfile.TemporaryDirectory() as temp_dir:
        print("Using Temp Dir : " + str(temp_dir))
        numfiles = len(files)
        for file in files:
            file_path = os.path.join(temp_dir, file.filename)
            with open(file_path, "wb") as buffer:
                shutil.copyfileobj(file.file, buffer)

        metadata_file_path = os.path.join(temp_dir,"metadata.json")
        with open(metadata_file_path, "w") as metadata_file:
            json.dump(metadata_dict, metadata_file)
        if len(os.listdir(temp_dir)) >0:
            upload_directory_to_s3(temp_dir,s3_url,bucket_name,access_key_id,secret_access_key)

    return f"Files uploaded successfully : {numfiles} Files"
