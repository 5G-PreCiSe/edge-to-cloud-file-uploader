import psutil
from uploader import Uploader
from oled import OLED
from filebrowser import FileBrowser
import json
from led import Led

from gpiozero import Button
import time

import threading

access_key = ""
secret_key = ""
path = "/media/user/images/last/"
bucket = "test"
device = "/dev/sdb1"
mnt_state = False

led = Led()

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
    

if __name__ == "__main__":

    
    led.set_color(255,0,0)
    button = Button(24)
    
    button.when_pressed = pressed
    button.when_released = released

    oled = OLED()
    
    t = threading.Thread(target=mount_observer, args=(1,), daemon=True)
    t.start()
    
    while True:
        print(mnt_state)
        if mnt_state:
            oled.draw("10 of 1203","Mounted","5G")
        else:
            oled.draw("10 of 1203","Unmounted","5G")
        oled.update()
        time.sleep(1)
        

    browser = FileBrowser()
    print(json.dumps(browser.browse_dir("/media","media","dir",0,0,0)))
    
    #upload = Uploader(access_key,secret_key)
    #upload.upload(path,bucket)
    
    
