FROM minio/minio:latest

# Set environment variables for access key and secret key
ENV MINIO_ACCESS_KEY=accesskey
ENV MINIO_SECRET_KEY=secretkey

# Expose port 9000 for MinIO server
EXPOSE 9000
EXPOSE 9001

# Set the default bucket name (optional)
ENV MINIO_BUCKET=mybucket

# Command to run MinIO server
CMD ["server","--console-address",":9001", "/data"]