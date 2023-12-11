
from board import SCL, SDA
import busio
from PIL import Image, ImageDraw, ImageFont
import adafruit_ssd1306
import time


class OLED:
    def __init__(self):
        i2c = busio.I2C(SCL,SDA)
        self.display = adafruit_ssd1306.SSD1306_I2C(128, 32, i2c)
        self.clear()
        self.default_font = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
    
    def clear(self):
        self.display.fill(0)
        self.display.show()
    
    def update(self):
        self.display.show()
        
    def draw(self,text,text_mounted,text_network):
        #font = ImageFont.load_default()

        font_large = ImageFont.truetype(font=self.default_font,size=15)
        text_width, text_height = font_large.getsize(text=text)
        
        font_small = ImageFont.truetype(font=self.default_font,size=9)
        mounted_text_width, mounted_text_height = font_small.getsize(text_mounted)
        network_text_width, network_text_height = font_small.getsize(text_network)
        
        width = self.display.width
        height = self.display.height
        offset_y = 5
        image = Image.new("1",(width,height))
        draw = ImageDraw.Draw(image)
        
        #draw center text
        draw.rectangle((0, height/2 - text_height/2 + offset_y, width-1, height/2 + text_height/2), outline=0, fill=0)
        draw.text((width/2 - text_width/2,height/2 - text_height/2 + offset_y),text, font=font_large, fill=255)
        
        #draw header
        draw.rectangle((0, 0, width-1, 0+network_text_height), outline=0, fill=0)
        draw.text((0,0),text_mounted,font=font_small,fill=255)
        draw.text((width-1-network_text_width,0),text_network,font=font_small,fill=255)
        
        self.display.image(image)
    
        
        
        