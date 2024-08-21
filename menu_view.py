from oled import OLED
from configuration_handler import ConfigurationHandler

class MenuView:

    VIEW_NETWORK_SETTINGS = 0
    VIEW_MQTT_SETTINGS = 1
    VIEW_FS_SETTINGS = 2
    VIEW_S3_SETTINGS = 3
    VIEW_SHUTDOWN = 4
    VIEW_REBOOT = 5

    FIRST_VIEW = VIEW_NETWORK_SETTINGS
    LAST_VIEW = VIEW_REBOOT

    def __init__(self,oled: OLED):
        self.oled = oled
        self.current_view = 0
        self.children = {}

    def add_child(self, id: int, label: str, view):
        self.children[id] = (label,view)

    def update(self):
        view_item = self.children[self.current_view]
        self.oled.draw_menu(view_item[0])
        self.oled.update()

    def next_view(self):
        self.current_view+=1
        if self.current_view > MenuView.LAST_VIEW:
            self.current_view = MenuView.FIRST_VIEW
    
    def previous_view(self):
        self.current_view-=1
        if self.current_view < MenuView.FIRST_VIEW:
            self.current_view = MenuView.LAST_VIEW
    
    def close(self,enter):
        return self.children[self.current_view][1]
    