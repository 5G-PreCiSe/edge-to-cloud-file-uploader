import psutil
from uploader import S3Uploader
from oled import OLED
from led import Led
from filesystem import FileSystem
import json

#from services.configuration_service import ConfigurationService
from configuration_handler import ConfigurationHandler
from mqtt import Mqtt
from api import Api

from gpiozero import Button
import time

import threading
import logging

from urllib import request

from main_view import MainView
from menu_view import MenuView
from mqtt_view import MqttView
from s3_view import S3View
from fs_view import FsView
from net_view import NetView
from shutdown_view import ShutdownView
from view_manager import ViewManager

led = Led()
oled = OLED()
btn_e = Button(6,pull_up=False)
btn_c = Button(5,pull_up=False)
btn_l = Button(13,pull_up=False)
btn_r = Button(19,pull_up=False)

#mqtt_connected = False
#mounted = False
s3_state = ""
registered = False
led_color = ()

main_view = MainView(oled,led)
menu_view = MenuView(oled)
mqtt_view = MqttView(oled)
s3_view = S3View(oled)
fs_view = FsView(oled)
net_view = NetView(oled)
shutdown_view = ShutdownView(oled,True)
reboot_view = ShutdownView(oled,False)

view_manager = ViewManager()

def pressed_e():
    logging.info("Enter button pressed")
    oled.wake_display()
    view_manager.btn_enter_pressed()
def pressed_c():
    logging.info("Cancel button pressed")
    oled.wake_display()
    view_manager.btn_cancel_pressed()
def pressed_l():
    logging.info("Left button pressed")
    oled.wake_display()
    view_manager.btn_left_pressed()
def pressed_r():
    logging.info("Right button pressed")
    oled.wake_display()
    view_manager.btn_right_pressed()


def mount_observer(cancel_event, configuration):
    while not cancel_event.is_set():
        found = False
        device = configuration.get("fs","Device")
        for item in psutil.disk_partitions():
            if item.device == device:
                found = True
        if found:
            mounted = True
        else:
            mounted = False
        fs_view.set_mount_state(mounted)
        main_view.mount_callback(mounted)
        net_view.network_callback(psutil.net_if_addrs())
        time.sleep(1)

def network_observer(cancel_event):
    while not cancel_event.is_set():
        net_view.network_callback(psutil.net_if_addrs())
        time.sleep(5)

'''
def s3_update_callback(job_id,total,completed,path):
    global s3_state

    oled.wake_display()
    s3_state = str(completed)+" of "+str(total)
    
def registered_callback():
    global registered
    global s3_state

    registered = True
    
    oled.wake_display()

    if mqtt_connected and mounted:
        s3_state = "Ready"
        led.set_color(0,255,0)
    elif not mounted:
        s3_state = "Card unmounted"
    elif not mqtt_connected:
        s3_state = "No connection"

def s3_status_callback(jobId,state):
    
    oled.wake_display()

    global s3_state
    if state == S3Uploader.JOB_SCHEDULED:
        pass
    elif state == S3Uploader.JOB_LOADED:
        s3_state = "Upload started"
    elif state == S3Uploader.JOB_IN_PROGRESS:
        pass
    elif state == S3Uploader.JOB_COMPLETED:
        #s3_state = "Completed"
        registered_callback()
        #oled.draw("Completed","Mounted","5G")
        led.set_color(0,255,0)
    elif state == S3Uploader.JOB_MANUALLY_CANCELED:
        s3_state = "Canceled"
        #oled.draw("Canceled","Mounted","5G")
        led.set_color(255,0,0)
    elif state == S3Uploader.JOB_SHUTDOWN_CANCELED:
        s3_state = "Shutting down"
        #oled.draw("Shutting down","Mounted","5G")
        led.set_color(255,0,0)
    elif state == S3Uploader.JOB_ERROR:
        s3_state = "Error"
        #oled.draw("Error","Mounted","5G")
        led.set_color(255,0,0)
    else:
        s3_state = "Unknown"
        #oled.draw("Unknown","Mounted","5G")
    #oled.update()

def mqtt_connection_callback(connected):
    global mqtt_connected
    mqtt_connected = connected

'''
    
def hid_worker(cancel_event):
    while not cancel_event.is_set():    
        view_manager.oled_update()
        time.sleep(0.1)
        '''
        if mounted:
            mnt_state = "Mounted"
        else:
            mnt_state = "Unmounted"
            led.set_color(255,0,0)
            
        if mqtt_connected:
            mqtt_state = "MQTT"
        else:
            mqtt_state = "X"
            led.set_color(255,0,0)
    
        if registered:
            #fs_view.draw_view()
            #mqtt_view.draw_view()
            oled.draw_main(s3_state,mnt_state,mqtt_state)
        else:
            oled.draw_main("Reg. pending", mnt_state,mqtt_state)
            
        
        oled.update()
        led.update()
        time.sleep(0.1)
        '''
    oled.draw_main("Shutting down", "","")
    oled.update()     

if __name__ == "__main__":
    
    format = "%(asctime)s: %(message)s"
    logging.basicConfig(format=format, level=logging.INFO,datefmt="%H:%M:%S")

    oled.draw_main("Initializing","","")
    oled.update()
    led.set_color(255,128,0)
    led.update()

    btn_e.when_pressed = pressed_e
    btn_c.when_pressed = pressed_c
    btn_l.when_pressed = pressed_l
    btn_r.when_pressed = pressed_r
    
    configuration = ConfigurationHandler()
    configuration.load_persistent_config("/home/user/workspace/edge-to-cloud-file-uploader/config.ini")
    s3_view.set_configuration(configuration)
    fs_view.set_configuration(configuration)
    mqtt_view.set_configuration(configuration)

    cancel_event = threading.Event()
    
    mount_observer_thread = threading.Thread(target=mount_observer, args=(cancel_event,configuration), daemon=False)
    mount_observer_thread.start()

    network_observer_thread = threading.Thread(target=network_observer, args=(cancel_event,), daemon=False)
    network_observer_thread.start()
    
    menu_view.add_child(MenuView.VIEW_MQTT_SETTINGS,"MQTT Settings",mqtt_view)
    menu_view.add_child(MenuView.VIEW_S3_SETTINGS,"Upload Settings",s3_view)
    menu_view.add_child(MenuView.VIEW_FS_SETTINGS,"Memory Card",fs_view)
    menu_view.add_child(MenuView.VIEW_NETWORK_SETTINGS,"Network Settings",net_view)
    menu_view.add_child(MenuView.VIEW_SHUTDOWN,"Shutdown",shutdown_view)
    menu_view.add_child(MenuView.VIEW_REBOOT,"Reboot",reboot_view)
    main_view.set_menu(menu_view)
    view_manager.open_view(main_view)

    hid_thread = threading.Thread(target=hid_worker, args=(cancel_event,), daemon=False)
    hid_thread.start()
    
    active_connection = False
    
    led_off = False
    while not active_connection:
        try:
            request.urlopen("http://www.google.com", timeout=1)
            active_connection = True
            if led_off:
                led.set_color(0,0,0)
            else:
                led.set_color(255,128,0)
            led.update()
            led_off != led_off
        except Exception as err:
            active_connection = False
    
    led.set_color(255,128,0)
    led.update()
    
    mqtt = Mqtt()
    mqtt.add_status_callback(mqtt_view.mqtt_connection_callback)
    mqtt.add_status_callback(main_view.mqtt_connection_callback)
    mqtt_connected = False
    while not mqtt_connected:
        mqtt_connected = mqtt.connect(configuration.get("broker","Address"),configuration.get("broker","Port",type="int"),configuration.get("device","DeviceId"),configuration.get("broker","Username"),configuration.get("broker","Password"))
    api = Api(configuration,mqtt)
    api.set_registered_callback(main_view.registration_callback)
    
    fs = FileSystem(configuration)
    api.set_filesystem(fs)
    
    s3 = S3Uploader(configuration)
    s3.add_update_callback(main_view.s3_update_callback)
    s3.add_status_callback(main_view.s3_status_callback)
    s3.add_status_callback(s3_view.s3_status_callback)
    api.set_uploader(s3)
    
    api.start(cancel_event)
    shutdown_view.set_api(api)
    reboot_view.set_api(api)

    oled.set_display_mode(display_mode=configuration, display_on_duration=configuration.get("device","DisplayOnDuration","int"),cancel_event=cancel_event)
    mqtt.start(cancel_event) # This call blocks the execution
    
    
    
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
