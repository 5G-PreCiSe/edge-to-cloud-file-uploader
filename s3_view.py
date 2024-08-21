from oled import OLED
from configuration_handler import ConfigurationHandler
from uploader import S3Uploader

class S3View:

    VIEW_SERVER = 0
    VIEW_STATS = 1

    FIRST_VIEW = VIEW_SERVER
    LAST_VIEW = VIEW_STATS

    def __init__(self,oled: OLED):
        self.oled = oled
        self.current_view = 0
        self.jobs_completed = 0

    def set_configuration(self,configuration):
        self.configuration = configuration

    def s3_status_callback(self,job_id,status):
        if status == S3Uploader.JOB_COMPLETED:
            self.jobs_completed+=1

    def update(self):
        if self.current_view == S3View.VIEW_SERVER:
            self.oled.draw_info("Upload Settings",["Server: "+self.configuration.get("s3","Server")])
        elif self.current_view == S3View.VIEW_STATS:
            self.oled.draw_info("Upload Settings",["Completed jobs: "+str(self.jobs_completed)])
        
        self.oled.update()

    def next_view(self):
        self.current_view+=1
        if self.current_view > S3View.LAST_VIEW:
            self.current_view = S3View.FIRST_VIEW
    
    def previous_view(self):
        self.current_view-=1
        if self.current_view < S3View.FIRST_VIEW:
            self.current_view = S3View.LAST_VIEW
    
    def close(self,enter):
        return None

    