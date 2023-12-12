from gpiozero import RGBLED

class Led:
    
    def __init__(self, red_gpio = 22, green_gpio = 27,blue_gpio = 17):
        self.led = RGBLED(red=red_gpio,green=green_gpio,blue=blue_gpio)
    
    def set_color(self,red,green,blue):
        self.led.color = (red/255,green/255,blue/255)