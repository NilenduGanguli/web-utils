import boto3

class S3Browser:
    def __init__(self, endpoint, access_key, secret_key, secure=False):
        self.s3 = boto3.client(
            's3',
            endpoint_url=endpoint,
            aws_access_key_id=access_key,
            aws_secret_access_key=secret_key,
            verify=secure
        )

    def list_objects(self, bucket_name):
        try:
            objects = self.s3.list_objects_v2(Bucket=bucket_name)
            if 'Contents' in objects:
                for obj in objects['Contents']:
                    print(obj['Key'])
            else:
                print("Bucket is empty.")
        except Exception as e:
            print(f"Error listing objects: {e}")

    def fetch_object(self, bucket_name, object_name, destination_file):
        try:
            self.s3.download_file(bucket_name, object_name, destination_file)
            print(f"Object {object_name} fetched to {destination_file}")
        except Exception as e:
            print(f"Error fetching object: {e}")

if __name__ == "__main__":
    # Initialize S3Browser with MinIO server details
    endpoint = "http://localhost:9000"  # MinIO server endpoint
    access_key = "accesskey"
    secret_key = "secretkey"
    secure = False  # Change to True if using SSL/TLS

    s3_browser = S3Browser(endpoint, access_key, secret_key, secure)

    # Example usage
    bucket_name = "test1"
    print("Listing objects in bucket:")
    s3_browser.list_objects(bucket_name)

    # object_name = "example.txt"  # Object to fetch
    # destination_file = "example.txt"  # Destination file path
    # print(f"Fetching object {object_name} from bucket {bucket_name}")
    # s3_browser.fetch_object(bucket_name, object_name, destination_file)
