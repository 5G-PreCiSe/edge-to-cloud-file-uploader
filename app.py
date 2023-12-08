import psutil
from uploader import Uploader

access_key = ""
secret_key = ""
path = "/media/user/images/last/"
bucket = "test"

if __name__ == "__main__":
    upload = Uploader(access_key,secret_key)
    upload.upload(path,bucket)
    
    
