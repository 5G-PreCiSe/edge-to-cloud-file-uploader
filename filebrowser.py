import os
import time

class FileBrowser:
    
    def __init__(self):
        pass
    
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
                    
                    entry_obj["entries"].append(self.browse_dir(entry.path,entry.name,t,stats.st_size,stats.st_ctime,stats.st_mtime))
        return entry_obj

