
from board import SCL, SDA
import busio
from PIL import Image, ImageDraw, ImageFont
import adafruit_ssd1306
import time
import threading


class OLED:

    DISPLAY_MODE_PERMANENT_OFF = 0
    DISPLAY_MODE_TEMPORARY_ON = 1
    DISPLAY_MODE_PERMANENT_ON = 2

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

    def _turn_on(self):
        self.display.poweron()
        self.update()
        
    def _turn_off(self):
        self.display.poweroff()

    def set_display_mode(self, display_mode: int, display_on_duration: int, cancel_event):
        if display_mode == OLED.DISPLAY_MODE_PERMANENT_OFF:
            self._turn_off()
        elif display_mode == OLED.DISPLAY_MODE_PERMANENT_ON:
            self._turn_on()
        else:
            self._turn_on()
            self.timer = threading.Thread(target=self._timer_ellapsed, args=(cancel_event,), daemon=False)
            self.lock = threading.Lock()
            self.display_on_duration = display_on_duration
            self.display_on_counter = self.display_on_duration
            self.timer.start()
        
    def _timer_ellapsed(self, cancel_event):
        while not cancel_event.is_set():
            try:
                self.lock.acquire()
                if self.display_on_counter > 0:
                    self.display_on_counter-=1
                else:
                    self._turn_off()

                #if self.display_on_counter == 0:
                #    self._turn_off()
                #elif self.display_on_counter == -1: # prevent overflow
                #    self.display_on_counter = -1
            finally:
                self.lock.release()
            time.sleep(1)

    def wake_display(self):
        self._turn_on() 
        try:
            self.lock.acquire()
            self.display_on_counter = self.display_on_duration
        finally:
            self.lock.release()
    
    def draw_header(self, text_left, text_right, draw: ImageDraw):
        font_small = ImageFont.truetype(font=self.default_font,size=9)
        width = self.display.width
        height = self.display.height

        if text_left:
            text_left_width, text_left_height = font_small.getsize(text_left)
            draw.text((0,0),text_left,font=font_small,fill=255)
        if text_right:
            text_right_width, text_right_height = font_small.getsize(text_right)
            draw.text((width-1-text_right_width,0),text_right,font=font_small,fill=255)

    def draw_main(self,text,text_mounted,text_network):

        font_large = ImageFont.truetype(font=self.default_font,size=15)
        text_width, text_height = font_large.getsize(text=text)
        
        #font_small = ImageFont.truetype(font=self.default_font,size=9)
        #mounted_text_width, mounted_text_height = font_small.getsize(text_mounted)
        #network_text_width, network_text_height = font_small.getsize(text_network)
        
        width = self.display.width
        height = self.display.height
        offset_y = 5
        image = Image.new("1",(width,height))
        draw = ImageDraw.Draw(image)
        
        #draw center text
        #draw.rectangle((0, height/2 - text_height/2 + offset_y, width-1, height/2 + text_height/2), outline=0, fill=0)
        draw.text((width/2 - text_width/2,height/2 - text_height/2 + offset_y),text, font=font_large, fill=255)
        self.draw_header(text_mounted, text_network, draw)

        #draw header
        #draw.rectangle((0, 0, width-1, 0+network_text_height), outline=0, fill=0)
        #draw.text((0,0),text_mounted,font=font_small,fill=255)
        #draw.text((width-1-network_text_width,0),text_network,font=font_small,fill=255)
        
        self.display.image(image)
    
    def draw_info(self, header, lines: list):
        font_small = ImageFont.truetype(font=self.default_font,size=9)
        width = self.display.width
        height = self.display.height
        
        offset_y = 0
        text_width, text_height = font_small.getsize(header)
        text_width_btn, _ = font_small.getsize(">")

        image = Image.new("1",(width,height))
        draw = ImageDraw.Draw(image)

        draw.text((0,-2),"<", font=font_small, fill=255)
        draw.text((width-1-text_width_btn,-2),">", font=font_small, fill=255)
        draw.text((width/2 - text_width/2,-1),header, font=font_small, fill=255)

        for i, line in enumerate(lines):
            draw.text((0,(text_height*(i+1))+offset_y),line, font=font_small, fill=255)
        
        self.display.image(image)
