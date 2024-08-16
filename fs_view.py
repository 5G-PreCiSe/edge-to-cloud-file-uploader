from oled import OLED
from configuration_handler import ConfigurationHandler

class FsView:

    VIEW_DEVICE = 0
    VIEW_MOUNT = 1
    VIEW_STATE = 2

    FIRST_VIEW = VIEW_DEVICE
    LAST_VIEW = VIEW_STATE

    def __init__(self,oled: OLED):
        self.oled = oled
        self.current_view = 0
        self.mounted = False

    def set_configuration(self,configuration):
        self.configuration = configuration

    def set_mount_state(self, is_mounted):
        self.mounted = is_mounted

    def draw_view(self,):
        if self.current_view == FsView.VIEW_DEVICE:
            self.oled.draw_info("Memory Card",["Device: "+self.configuration.get("fs","Device")])
        elif self.current_view == FsView.VIEW_MOUNT:
            self.oled.draw_info("Memory Card",["Mount point: "+self.configuration.get("fs","Mount"),"File system: "+self.configuration.get("fs","FileSystem")])
        elif self.current_view == FsView.VIEW_STATE:
            if self.mounted:
                self.oled.draw_info("Memory Card",["State: Mounted"])
            else: 
                self.oled.draw_info("Memory Card",["State: Unmounted"])
        self.oled.update()

    def next_view(self):
        self.current_view+=1
        if self.current_view > FsView.LAST_VIEW:
            self.current_view = FsView.FIRST_VIEW
    
    def previous_view(self):
        self.current_view-=1
        if self.current_view < FsView.FIRST_VIEW:
            self.current_view = FsView.LAST_VIEW
    