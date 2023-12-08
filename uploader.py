from minio import Minio
from minio.error import S3Error
import os
class Uploader:
    
    def __init__(self,access_key, secret_key,s3_uri = "s3.5g-precise.de"):
        self.client = Minio(s3_uri,access_key=access_key,secret_key=secret_key,secure=False)
        
    def upload(self,path,bucket):
        found = self.client.bucket_exists(bucket)
        if not found:
            self.client.make_bucket(bucket)
        
        for file in os.listdir(path):
            print("Upload ",os.path.join(path,file))
            self.client.fput_object(bucket,file,os.path.join(path,file))
        
        
        
