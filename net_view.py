from oled import OLED
from configuration_handler import ConfigurationHandler
import psutil

class NetView:

    def __init__(self,oled: OLED):
        self.oled = oled
        self.current_view = 0
        self.num_infs = 0
        self.interfaces = []

    def network_callback(self,interfaces):
        num_interfaces = 0
        self.interfaces.clear()
        for key in interfaces.keys():
            if key != 'lo':
                num_interfaces+=1
                self.interfaces.append((key,interfaces[key][0].address))
        self.num_infs = num_interfaces
        if self.current_view > self.num_infs:
            self.current_view = self.num_inf

    def update(self):
        if self.interfaces:
            if self.current_view < len(self.interfaces):
                self.oled.draw_info("Network Settings",["Name: "+self.interfaces[self.current_view][0],"Addr: "+self.interfaces[self.current_view][1]])
        else:
            self.oled.draw_info("Network Settings",["No interfaces"]) 

    def next_view(self):
        self.current_view+=1
        if self.current_view > len(self.interfaces)-1:
            self.current_view = 0
    
    def previous_view(self):
        self.current_view-=1
        if self.current_view < 0:
            self.current_view = len(self.interfaces)-1
    
    def close(self,enter):
        return None
    