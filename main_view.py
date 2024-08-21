from oled import OLED
from led import Led
from uploader import S3Uploader

class MainView:

    def __init__(self, oled: OLED, led: Led):
        self.oled = oled
        self.connected = False
        self.mounted = False
        self.s3_state = "Waiting for reg."
        self.led = led

    def set_menu(self,view):
        self.menu = view

    def registration_callback(self):
        self.oled.wake_display()
        if self.connected and self.mounted:
            self.s3_state = "Ready"
            self.led.set_color(0,255,0)
        elif not self.connected:
            self.s3_state = "No connection"
            self.led.set_color(255,0,0)
        elif not self.mounted:
            self.s3_state = "Card unmounted"
            self.led.set_color(255,128,0)
        self.led.update()

    def s3_status_callback(self,job_id, state):
        self.oled.wake_display()
        if state == S3Uploader.JOB_SCHEDULED:
            pass
        elif state == S3Uploader.JOB_LOADED:
            self.s3_state = "Upload started"
        elif state == S3Uploader.JOB_IN_PROGRESS:
            pass
        elif state == S3Uploader.JOB_COMPLETED:
            self.s3_state = "Upload compl."
            self.led.set_color(0,255,0)
        elif state == S3Uploader.JOB_MANUALLY_CANCELED:
            self.s3_state = "Canceled"
            self.led.set_color(0,255,0)
        elif state == S3Uploader.JOB_SHUTDOWN_CANCELED:
            self.s3_state = "Shutting down"
            self.led.set_color(255,128,0)
        elif state == S3Uploader.JOB_ERROR:
            self.s3_state = "Error"
            self.led.set_color(255,0,0)
        else:
            self.s3_state = "Unknown"
        self.led.update()

    def s3_update_callback(self,job_id,total,completed,path):
        self.oled.wake_display()
        self.s3_state = str(completed)+" of "+str(total)
        self.led.set_color(0,128,255)
        self.led.update()

    def mount_callback(self, mounted):
        self.mounted = mounted

    def mqtt_connection_callback(self,connected):
        self.connected = connected

    def update(self):
        mnt_state = "Unmounted"
        if self.mounted:
            mnt_state = "Mounted"
        mqtt_state = "X"
        if self.connected:
            mqtt_state = "MQTT"
        self.oled.draw_main(self.s3_state,mnt_state,mqtt_state)
        self.oled.update()
        self.led.update()        

    def next_view(self):
        pass
    
    def previous_view(self):
        pass
    
    def close(self,enter):
        return self.menu