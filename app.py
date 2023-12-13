import psutil
from uploader import S3Uploader
from oled import OLED
from filesystem import FileSystem
import json
from led import Led

from gpiozero import Button
import time

import threading
import logging

access_key = ""
secret_key = ""
path = "/media/user/images/last/"
bucket = "test"
device = "/dev/sdb1"
mnt_state = False

led = Led()
oled = OLED()

def pressed():
    print("Pressed")

def released():
    print("released")


def mount_observer(name):
    global mnt_state
    while True:
        found = False
        for item in psutil.disk_partitions():
            if item.device == device:
                found = True
        if found:
            print("Device ",device," is present")
            led.set_color(0,255,0)
            mnt_state = True
        else:
            print("Device is not present")
            led.set_color(255,0,0)
            mnt_state = False
        time.sleep(1)

def update_callback(total,completed):
    oled.draw(str(completed)+" of "+str(total),"Mounted","5G")
    led.set_color(128,128,0)
    oled.update()
    
def status_callback(state):
    if state == S3Uploader.JOB_COMPLETED:
        oled.draw("Completed","Mounted","5G")
        led.set_color(0,255,0)
    elif state == S3Uploader.JOB_MANUALLY_CANCELED:
        oled.draw("Canceled","Mounted","5G")
        led.set_color(255,0,0)
    elif state == S3Uploader.JOB_SHUTDOWN_CANCELED:
        oled.draw("Shutting down","Mounted","5G")
        led.set_color(255,0,0)
    elif state == S3Uploader.JOB_EXCEPTION_CANCELED:
        oled.draw("Error","Mounted","5G")
        led.set_color(255,0,0)
    else:
        oled.draw("Unknown","Mounted","5G")
        led.set_color(255,0,0)
    oled.update()

if __name__ == "__main__":
    
    format = "%(asctime)s: %(message)s"
    logging.basicConfig(format=format, level=logging.INFO,datefmt="%H:%M:%S")
    
    s3 = S3Uploader(access_key,secret_key)
    s3.set_update_callback(update_callback)
    s3.set_status_callback(status_callback)

    cancel_event = threading.Event()
    upload_worker_thread = threading.Thread(target=s3.upload_worker,args=(cancel_event,),daemon=False)
    upload_worker_thread.start()
    
    job = {
        "jobId":"123",
        "bucket":"2023-12-13",
        "path": "/media/user/BAE4-A49C/images/last/"
    }
    
    s3.add_job(job)
    time.sleep(10)
    cancel_event.set()
    time.sleep(10)
    
    '''
    led.set_color(255,0,0)
    button = Button(24)
    
    button.when_pressed = pressed
    button.when_released = released

    
    
    t = threading.Thread(target=mount_observer, args=(1,), daemon=True)
    t.start()
    
    #while True:
    print(mnt_state)
    if mnt_state:
        oled.draw("10 of 1203","Mounted","5G")
    else:
        oled.draw("10 of 1203","Unmounted","5G")
    oled.update()
    time.sleep(1)
    

    browser = FileSystem()
    print(json.dumps(browser.browse_dir("/media","media","dir",0,0,0)))
    
    #upload = Uploader(access_key,secret_key)
    #upload.upload(path,bucket)
    '''