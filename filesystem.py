import os
import time
import sh
import psutil
import datetime

class FileSystem:
    
    def __init__(self):
        pass
    
    def mount_drive(self, device_path, mount_path, filesystem = "exfat"):
        sh.sudo.mount(device_path,mount_path,"-t"+filesystem)
    
    def umount_drive(self, mount_path):
        sh.sudo.umount(mount_path)
        
    def is_mounted(device_path):
        found = False
        for item in psutil.disk_partitions():
            if item.device == device_path:
                found = True
        return found
    
    def scan_drive(self, mount_path):
        return self.browse_dir(mount_path,"root","dir",0,0,0)
    
    def browse_dir(self, path, name, ttype, size, created, modified):
        entry_obj = {
            "path": path,
            "name": name,
            "type": ttype,
            "size": size,
            "created": created,
            "modified": modified
        }
        if ttype == "dir":
            entry_obj["entries"] = []
            
            with os.scandir(path) as it:
                for entry in it:
                    t = None
                    if entry.is_dir():
                        t = "dir"
                    elif entry.is_file():
                        t = "file"
                    elif entry.is_junction():
                        t = "junction"
                    elif entry.is_symlink():
                        t = "symlink"
                    else:
                        t = "deleted"
                    stats = os.stat(entry.path)

                    creation_time_s = str(datetime.datetime.fromtimestamp(stats.st_ctime).isoformat())
                    modification_time_s = str(datetime.datetime.fromtimestamp(stats.st_mtime).isoformat())
                    
                    entry_obj["entries"].append(self.browse_dir(entry.path,entry.name,t,stats.st_size,creation_time_s,modification_time_s))
        return entry_obj

