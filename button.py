import RPi.GPIO as GPIO

class Button:
    
    def __init__(self, pin: int):
        self.pin = pin
        GPIO.setmode(GPIO.BOARD)
        GPIO.setup(self.pin, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
    
    def add_button_pressed_callback(self, callback):
        GPIO.add_event_detect(self.pin,GPIO.RISING,callback=callback) 

    def add_button_released_callback(self, callback):
        GPIO.add_event_detect(self.pin,GPIO.FALLING,callback=callback) 