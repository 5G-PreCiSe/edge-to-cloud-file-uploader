import os
import time
import sh
import psutil
import datetime
import json

from api import MissingArgumentException, UnknownCommandException

class FileSystem:
    
    def __init__(self, configuration_handler):
        self.configuration = configuration_handler
    
    def mount_drive(self, device_path, mount_path, filesystem = "exfat"):
        sh.sudo.mount(device_path,mount_path,"-t"+filesystem)
    
    def umount_drive(self, mount_path):
        sh.sudo.umount(mount_path)
        
    def is_mounted(self, device_path):
        found = False
        for item in psutil.disk_partitions():
            if item.device == device_path:
                found = True
        return found
    
    def scan_drive(self, mount_path):
        return self.browse_dir(mount_path,"root","dir",0,0,0)
    
    def browse_dir(self, path, name, ttype, size, created, modified, max_depth = -1):
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
            
            if max_depth != 0:
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
                        
                        entry_obj["entries"].append(self.browse_dir(entry.path,entry.name,t,stats.st_size,creation_time_s,modification_time_s,max_depth-1))
        return entry_obj
    
    def request(self, req_payload):
        
        if "command" in req_payload:
            if req_payload["command"] == "mount":
                response = self.cmd_mount(req_payload)
            elif req_payload["command"] == "umount":
                response = self.cmd_umount(req_payload)
            elif req_payload["command"] == "isMounted":
                response = self.cmd_is_mounted(req_payload)
            elif req_payload["command"] == "browse":
                response = self.cmd_browse(req_payload)
            else:
                raise UnknownCommandException(command=req_payload["command"])
        else:
            raise MissingArgumentException(argument="command")

        response["command"] = req_payload["command"]
        return response
    
    def cmd_mount(self, req_payload):
        if "devicePath" in req_payload:
            device_path = req_payload["devicePath"]
        else:
            device_path = self.configuration.get("fs","Device")
        
        if "mountPath" in req_payload:
            mount_path = req_payload["mountPath"]
        else:
            mount_path = self.configuration.get("fs","Mount")
        
        if "fileSystem" in req_payload:
            file_system = req_payload["fileSystem"]
        else:
            file_system = self.configuration.get("fs","FileSystem")
        
        self.mount_drive(device_path,mount_path,file_system)
        response = {
            "isMounted": self.is_mounted(device_path)
        }
        return response

    def cmd_umount(self, req_payload):
        if "devicePath" in req_payload:
            device_path = req_payload["devicePath"]
        else:
            device_path = self.configuration.get("fs","Device")
        
        if "mountPath" in req_payload:
            mount_path = req_payload["mountPath"]
        else:
            mount_path = self.configuration.get("fs","Mount")
        
        self.umount_drive(mount_path)
        response = {
            "isMounted": self.is_mounted(device_path)
        }
        return response
    
    def cmd_is_mounted(self, req_payload):
        if "devicePath" in req_payload:
            device_path = req_payload["devicePath"]
        else:
            device_path = self.configuration.get("fs","Device")
        
        response = {
            "isMounted": self.is_mounted(device_path)
        }
        return response
    
    def cmd_browse(self, req_payload):
        if "path" in req_payload:
            path = req_payload["path"]
        else:
            raise MissingArgumentException("path")
        
        entries = self.browse_dir(path,"","dir",0,0,0,max_depth=1)["entries"]
        response = {
            "content": entries
        }
        return response
