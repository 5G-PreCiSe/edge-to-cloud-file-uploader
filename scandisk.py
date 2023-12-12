import os
import time


class ScanDisk:
    
    def __init__(self):
        pass
    
    def scan_dir(self,path, name, root = False):
        results = dict()
        results.name = name
        results.path = path
        if root:
            results.type = 
        results.entries = []
        with os.scan_dir(path) as it:
            for entry in it:
                
    def 
                
        

def scan_dir(path):
    with os.scandir(path) as it:
        for entry in it:
            print(entry.path)
            if entry.is_dir():
                scan_dir(entry.path)

if __name__ == "__main__":
    scan_dir("/media/user")
    #for item in os.scandir("/media/user"):
    #    print(item.name)
    #    print(time.ctime(os.stat(item.path).st_ctime)) 
        
    

                
