import configparser

class ConfigurationService:
    
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

    
    
    