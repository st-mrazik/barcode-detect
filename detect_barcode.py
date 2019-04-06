import sys

sys.path.append("/home/pi/rpi_ws281x/python/build/lib.linux-armv7l-2.7")

import logging
import time
import datetime

import cv2
import imutils.video
import mercury
import pygsm

from pyzbar import pyzbar
from gpiozero import LED
from neopixel import *

from dronekit import connect

root = logging.getLogger()
root.setLevel(logging.INFO)

handler = logging.StreamHandler(sys.stdout)
handler.setLevel(logging.INFO)
formatter = logging.Formatter('%(levelname)s - %(message)s')
handler.setFormatter(formatter)
root.addHandler(handler)

vehicle = connect('/dev/ttyAMA0', wait_ready=True, baud=57600)

msg_open = vehicle.message_factory.command_long_encode(0, 0, 183, 0, 9, 2000, 0, 0, 0, 0, 0)

try:
    logging.info("Capturing stream from camera...")
    vs = imutils.video.VideoStream(usePiCamera=True).start()
except Exception as e:
    logging.error("Error: {e}".format(e=e))
    vs = None

led_status = 3 
led_camera = 2
led_rfid = 1
led_gsm = 0
time.sleep(2)

# LED strip configuration:
LED_COUNT      = 4      # Number of LED pixels.
LED_PIN        = 18      # GPIO pin connected to the pixels (18 uses PWM!).
#LED_PIN        = 10      # GPIO pin connected to the pixels (10 uses SPI /dev/spidev0.0).
LED_FREQ_HZ    = 800000  # LED signal frequency in hertz (usually 800khz)
LED_DMA        = 10      # DMA channel to use for generating signal (try 10)
LED_BRIGHTNESS = 255     # Set to 0 for darkest and 255 for brightest
LED_INVERT     = False   # True to invert the signal (when using NPN transistor level shift)
LED_CHANNEL    = 0       # set to '1' for GPIOs 13, 19, 41, 45 or 53
LED_INTENSITY  = 80  

display_video = False 

try:
    reader = mercury.Reader("tmr:///dev/ttyUSB0")
    reader.set_region("EU3")
    reader.set_read_plan([1], "GEN2")
except Exception as e:
    logging.error("Error: {e}".format(e=e))
    reader = None


try:
    gsm_modem = pygsm.GsmModem(port="/dev/ttyUSB1")
    gsm_modem.boot()
except Exception as e:
    logging.error("Error: {e}".format(e=e))
    gsm_modem = None

# Define functions which animate LEDs in various ways.
def colorWipe(strip, color, wait_ms=50):
    """Wipe color across display a pixel at a time."""
    for i in range(strip.numPixels()):
        strip.setPixelColor(i, color)
        strip.show()
        time.sleep(wait_ms/1000.0)

def setColor(strip, index, color, wait_ms=50):
    led_range = range(strip.numPixels())
    i = led_range[index]
    strip.setPixelColor(i, color)
    strip.show()
    time.sleep(wait_ms/1000.0)

# Create NeoPixel object with appropriate configuration.
strip = Adafruit_NeoPixel(LED_COUNT, LED_PIN, LED_FREQ_HZ, LED_DMA, LED_INVERT, LED_BRIGHTNESS, LED_CHANNEL)
# Intialize the library (must be called once before other functions).
strip.begin()

i = 0
gsm_timer = datetime.datetime.now()
colorWipe(strip, Color(0, 0, 0))
setColor(strip, led_status, Color(LED_INTENSITY, 0, 0))
while True:
    if vs is not None:
        frame = vs.read()
        if i % 10 == 0:
            barcodes = pyzbar.decode(frame)

            for barcode in barcodes:
                barcodeData = barcode.data.decode("utf-8")
                barcodeType = barcode.type.decode("utf-8")

                if display_video:
                    (x, y, w, h) = barcode.rect
                    cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 0, 255), 2)

                    text = u"{} ({})".format(barcodeData, barcodeType)
                    cv2.putText(frame, text.encode("ascii", errors="replace"), (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 2)
     
                logging.info(u"Found {type_} barcode: {data}".format(type_=barcodeType, data=barcodeData))

            if barcodes and [val for val in barcodes if "open" in val]:
                setColor(strip, led_camera, Color(LED_INTENSITY, LED_INTENSITY, LED_INTENSITY))
		vehicle.send_mavlink(msg_open)
            else:
                setColor(strip, led_camera, Color(0, 0, 0))

            if display_video:
                cv2.imshow('frame',frame)
                if cv2.waitKey(1) & 0xFF == ord('q'):
                    break
    else:
        if i % 2 == 0:
            setColor(strip, led_camera, Color(0, LED_INTENSITY, 0))
        else:
            setColor(strip, led_camera, Color(0, 0, 0))

    if reader is not None:
        if i % 20 == 0:	
            rfid_codes = reader.read()
            if rfid_codes:
                logging.info(u"Found RFID {data}".format(data=rfid_codes))
                setColor(strip, led_rfid, Color(0, 0, LED_INTENSITY))
		vehicle.send_mavlink(msg_open)
            else:
                setColor(strip, led_rfid, Color(0, 0, 0))
    else:
       if i % 2 == 0: 
           setColor(strip, led_rfid, Color(0, LED_INTENSITY, 0))
       else:
           setColor(strip, led_rfid, Color(0, 0, 0))


    if gsm_modem is not None:
        if i % 50 == 0:
            sms_data = gsm_modem.next_message()
            if sms_data and "Land" in str(sms_data):
                logging.info(u"SMS: {data}".format(data=sms_data))
                gsm_timer = datetime.datetime.now()
                setColor(strip, led_gsm, Color(0, LED_INTENSITY, 0))
		vehicle.send_mavlink(msg_open)
            if datetime.datetime.now() - gsm_timer >= datetime.timedelta(seconds=5):
                setColor(strip, led_gsm, Color(0, 0, 0))
    else:
        if i % 2 == 0:
            setColor(strip, led_gsm, Color(0, LED_INTENSITY, 0))
        else:
            setColor(strip, led_gsm, Color(0, 0, 0))

    i += 1
    if i > 50:
        i = 0
