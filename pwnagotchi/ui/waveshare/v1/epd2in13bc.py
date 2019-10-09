# *****************************************************************************
# * | File        :	  epd2in13bc.py
# * | Author      :   Waveshare team
# * | Function    :   Electronic paper driver
# * | Info        :   Updated by C. Diemel 10.2019
# *----------------
# * | This version:   V4.0
# * | Date        :   2019-06-20
# # | Info        :   python demo
# -----------------------------------------------------------------------------
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documnetation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to  whom the Software is
# furished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS OR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.
#

import logging
from . import epdconfig

# Display resolution
EPD_WIDTH       = 104
EPD_HEIGHT      = 212

## 1 = debug on, 0 = debug off
## CAUTION: significant output from send_data function
DEBUG = 0

def init_logging(name, filename, stream_log):
    formatter = logging.Formatter("[%(asctime)s] [%(levelname)s] %(message)s")
    DispLog = logging.getLogger(name)

    DispLog.setLevel(logging.DEBUG)

    file_handler = logging.FileHandler(filename)
    file_handler.setFormatter(formatter)
    DispLog.addHandler(file_handler)
    
    if stream_log:
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        DispLog.addHandler(console_handler)
    
    DispLog.info("\n\n##########################\n\nInitiating logging\n\n##########################")
    
    return DispLog

class EPD:
    def __init__(self):
        if DEBUG :
            self.d_logger = init_logging("display_logger","/var/log/epd2in13.log", 1)

        self.reset_pin = epdconfig.RST_PIN
        self.dc_pin = epdconfig.DC_PIN
        self.busy_pin = epdconfig.BUSY_PIN
        self.cs_pin = epdconfig.CS_PIN
        self.width = EPD_WIDTH
        self.height = EPD_HEIGHT

        self.lut_full_update = [
            0x22, 0x55, 0xAA, 0x55, 0xAA, 0x55, 0xAA, 0x11,
            0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
            0x1E, 0x1E, 0x1E, 0x1E, 0x1E, 0x1E, 0x1E, 0x1E,
            0x01, 0x00, 0x00, 0x00, 0x00, 0x00
        ]

        self.lut_partial_update  = [
            0x18, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
            0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
            0x0F, 0x01, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00,
            0x00, 0x00, 0x00, 0x00, 0x00, 0x00
        ]

    # Hardware reset
    def reset(self): 
        if DEBUG :
            self.d_logger.debug("reset(self)")

        epdconfig.digital_write(self.reset_pin, 1)
        epdconfig.delay_ms(200) 
        epdconfig.digital_write(self.reset_pin, 0)
        epdconfig.delay_ms(10)
        epdconfig.digital_write(self.reset_pin, 1)
        epdconfig.delay_ms(200)  

    def send_command(self, command): 
        if DEBUG :
            self.d_logger.debug("send_command(self, command)")
            self.d_logger.debug(command)

        epdconfig.digital_write(self.dc_pin, 0)
        epdconfig.digital_write(self.cs_pin, 0)
        epdconfig.spi_writebyte([command])
        epdconfig.digital_write(self.cs_pin, 1)

    def send_data(self, data): 
        if DEBUG :
            self.d_logger.debug("send_data(self, data)")
            self.d_logger.debug(data)

        epdconfig.digital_write(self.dc_pin, 1)
        epdconfig.digital_write(self.cs_pin, 0)
        epdconfig.spi_writebyte([data])
        epdconfig.digital_write(self.cs_pin, 1)
        
    def ReadBusy(self): 
        if DEBUG :
            self.d_logger.debug("readBusy(self)")

        logging.debug("e-Paper busy")
        while(epdconfig.digital_read(self.busy_pin) == 0):      # 0: idle, 1: busy
            epdconfig.delay_ms(100)
        logging.debug("e-Paper busy release")

############################
####  had to change the function due to overloading
    def init(self, lut):
        if DEBUG :
            self.d_logger.debug("init(self)")
            self.d_logger.debug(lut)

        if (epdconfig.module_init() != 0):
            return -1
            
        self.reset()

        self.send_command(0x06) # BOOSTER_SOFT_START
        self.send_data(0x17)
        self.send_data(0x17)
        self.send_data(0x17)
        
        self.send_command(0x04) # POWER_ON
        self.ReadBusy()
        
        self.send_command(0x00) # PANEL_SETTING
        self.send_data(0x8F)
        
        self.send_command(0x50) # VCOM_AND_DATA_INTERVAL_SETTING
        self.send_data(0xF0)
        
        self.send_command(0x61) # RESOLUTION_SETTING
        self.send_data(self.width & 0xff)
        self.send_data(self.height >> 8)
        self.send_data(self.height & 0xff)
        
        # WRITE_LUT_REGISTER
        self.send_command(0x32)
        for count in range(30):
            self.send_data(lut[count])
        return 0

    def getbuffer(self, image):
        if DEBUG :
            self.d_logger.debug("getbuffer(self, image)")

        # logging.debug("bufsiz = ",int(self.width/8) * self.height)
        buf = [0xFF] * (int(self.width/8) * self.height)
        image_monocolor = image.convert('1')
        imwidth, imheight = image_monocolor.size
        pixels = image_monocolor.load()
        # logging.debug("imwidth = %d, imheight = %d",imwidth,imheight)
        if(imwidth == self.width and imheight == self.height):
            logging.debug("Vertical")
            for y in range(imheight):
                for x in range(imwidth):
                    # Set the bits for the column of pixels at the current position.
                    if pixels[x, y] == 0:
                        buf[int((x + y * self.width) / 8)] &= ~(0x80 >> (x % 8))
        elif(imwidth == self.height and imheight == self.width):
            logging.debug("Horizontal")
            for y in range(imheight):
                for x in range(imwidth):
                    newx = y
                    newy = self.height - x - 1
                    if pixels[x, y] == 0:
                        buf[int((newx + newy*self.width) / 8)] &= ~(0x80 >> (y % 8))
        return buf

#    def display(self, imageblack, imagered):
    def display(self, *argv):
        if DEBUG :
            self.d_logger.debug("display(self, imageblack, imagered)")
            self.d_logger.debug(argv[0])
        
        if len(argv) == 1:
            imageblack = argv[0]
            imagered = None
            
        if len(argv) == 2:
            imageblack = argv[0]
            imagered = argv[1]
        
        self.send_command(0x10)
        for i in range(0, int(self.width * self.height / 8)):
            self.send_data(imageblack[i])
        self.send_command(0x92)
        
        if imagered is not None:
            self.send_command(0x13)
            for i in range(0, int(self.width * self.height / 8)):
                self.send_data(imagered[i])
            self.send_command(0x92)
        
        self.send_command(0x12) # REFRESH
        self.ReadBusy()
        
    def Clear(self, color):
        if DEBUG :
            self.d_logger.debug("Clear(self, color)")
            self.d_logger.debug(color)

        self.send_command(0x10)
        for i in range(0, int(self.width * self.height / 8)):
            self.send_data(0xFF)
        self.send_command(0x92) 
        
        self.send_command(0x13)
        for i in range(0, int(self.width * self.height / 8)):
            self.send_data(0xFF)
        self.send_command(0x92)
        
        self.send_command(0x12) # REFRESH
        self.ReadBusy()

    def sleep(self):
        if DEBUG :
            self.d_logger.debug("sleep(self)")

        self.send_command(0x02) # POWER_OFF
        self.ReadBusy()
        self.send_command(0x07) # DEEP_SLEEP
        self.send_data(0xA5) # check code
        
        epdconfig.module_exit()
### END OF FILE ###


