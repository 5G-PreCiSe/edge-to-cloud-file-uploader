from gpiozero import RGBLED

class Led:
    
    def __init__(self, red_gpio = 22, green_gpio = 27,blue_gpio = 17):
        self.led = RGBLED(red=red_gpio,green=green_gpio,blue=blue_gpio)
    
    def set_color(self,red,green,blue):
        self.red = red
        self.green = green
        self.blue = blue
        
    def update(self):
        self.led.color = (self.red/255,self.green/255,self.blue/255)