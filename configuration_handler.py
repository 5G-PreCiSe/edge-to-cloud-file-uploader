import configparser

class ConfigurationHandler:
    
    def __init__(self):
        self.configuration = configparser.ConfigParser()
    
    def load_persistent_config(self, path):
        self.configuration.read(path)
        
    def get(self, section, key, type = "string"):
        if type == "int":
            return self.configuration.getint(section,key)
        elif type == "float":
            return self.configuration.getfloat(section,key)
        elif type == "boolean":
            return self.configuration.getboolean(section,key)
        else:
            return self.configuration[section][key]
    
    def request(self, req_payload):
        if "responseFileSystemTopic" in req_payload:
            self.configuration.set("api","responseFileSystemTopic", req_payload["responseFileSystemTopic"])
        if "requestFileSystemTopic" in req_payload:
            self.configuration.set("api","requestFileSystemTopic", req_payload["requestFileSystemTopic"])
        
        if "reponseJobsTopic" in req_payload:
            self.configuration.set("api","reponseJobsTopic", req_payload["reponseJobsTopic"])
        if "requestJobsTopic" in req_payload:
            self.configuration.set("api","requestJobsTopic", req_payload["requestJobsTopic"])

    

    
    
    