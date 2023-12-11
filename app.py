import psutil
from uploader import Uploader
from oled import OLED
from filebrowser import FileBrowser
import json

access_key = ""
secret_key = ""
path = "/media/user/images/last/"
bucket = "test"

if __name__ == "__main__":
    oled = OLED()
    oled.draw("10 of 1203","Mounted","5G")
    oled.update()
    
    browser = FileBrowser()
    print(json.dumps(browser.browse_dir("/media","media","dir",0,0,0)))
    
    #upload = Uploader(access_key,secret_key)
    #upload.upload(path,bucket)
    
    
