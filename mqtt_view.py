from oled import OLED
from configuration_handler import ConfigurationHandler

class MqttView:

    VIEW_BROKER = 0
    VIEW_USER = 1
    VIEW_STATE = 2

    FIRST_VIEW = VIEW_BROKER
    LAST_VIEW = VIEW_STATE

    def __init__(self,oled: OLED):
        self.oled = oled
        self.current_view = 0
        self.connected = False

    def set_configuration(self,configuration):
        self.configuration = configuration
    
    def mqtt_connection_callback(self,connected):
        self.connected = connected
    
    def update(self):
        if self.current_view == MqttView.VIEW_BROKER:
            self.oled.draw_info("MQTT Settings",["Broker: "+self.configuration.get("broker","Address"),"Port: "+str(self.configuration.get("broker","Port"))])
        elif self.current_view == MqttView.VIEW_USER:
            self.oled.draw_info("MQTT Settings",["Client: "+self.configuration.get("device","DeviceId"),"User: "+str(self.configuration.get("broker","Username"))])
        elif self.current_view == MqttView.VIEW_STATE:
            if self.connected:
                self.oled.draw_info("MQTT Settings",["State: Connected"])
            else: 
                self.oled.draw_info("MQTT Settings",["State: Disconnected"])
        self.oled.update()

    def next_view(self):
        self.current_view+=1
        if self.current_view > MqttView.LAST_VIEW:
            self.current_view = MqttView.FIRST_VIEW
    
    def previous_view(self):
        self.current_view-=1
        if self.current_view < MqttView.FIRST_VIEW:
            self.current_view = MqttView.LAST_VIEW
    
    def close(self,enter):
        return None
    