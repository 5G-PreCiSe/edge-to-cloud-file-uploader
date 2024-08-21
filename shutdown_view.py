from oled import OLED

class ShutdownView:

    def __init__(self,oled: OLED, shutdown = True):
        self.oled = oled
        self.api = None
        self.shutdown = shutdown

    def set_api(self, api):
        self.api = api

    def update(self):
        if self.shutdown:
            self.oled.draw_main("Shutdown?","[E]nter","[C]ancel")
        else:
            self.oled.draw_main("Reboot?","[E]nter","[C]ancel")
        self.oled.update()

    def next_view(self):
        pass
    
    def previous_view(self):
        pass
    
    def close(self, enter):
        if enter:
            if self.shutdown:
                self.api.shutdown()
            else:
                self.api.reboot()
        return None
    