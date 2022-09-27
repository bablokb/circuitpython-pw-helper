# ----------------------------------------------------------------------------
# main.py: main driver program
#
# Display: Waveshare Pico-0.96 LCD-display with joystick and two buttons
#          https://www.waveshare.com/wiki/Pico-LCD-0.96
#
# Other hardware requires other pins and probably a different display-driver
#
# Author: Bernhard Bablok
# License: GPL3
#
# Website: https://github.com/bablokb/circuitpython-pw-helper
#
# ----------------------------------------------------------------------------

import board
import time

# display libraries
import displayio
import busio
from adafruit_st7735r import ST7735R
import vectorio
from adafruit_display_text import label
from adafruit_bitmap_font import bitmap_font

# key-library
import keypad

# HID-libraries
import usb_hid
from adafruit_hid.keyboard  import Keyboard
from keyboard_layout_win_de import KeyboardLayout

# application library
from SecretsManager import SecretsManager as SecretsManager

# SPI/TFT pins
PIN_MOSI = board.GP11
PIN_CLK  = board.GP10
PIN_CS   = board.GP9
PIN_DC   = board.GP8
PIN_RST  = board.GP12
PIN_BL   = board.GP13

# TFT-characteristics
TFT_WIDTH  = 160
TFT_HEIGHT =  80
TFT_ROTATE =  90
TFT_BGR    = True

# button pins
PIN_USER  = board.GP15
PIN_PW    = board.GP17
PIN_UP    = board.GP2
PIN_DOWN  = board.GP18

# unused pins
PIN_LEFT  = board.GP16
PIN_RIGHT = board.GP20
PIN_ENTER = board.GP3

# fonts and colors
FONT   = bitmap_font.load_font("fonts/DejaVuSansMono-Bold-24.bdf")
BLACK  = 0x000000
WHITE  = 0xFFFFFF
RED    = 0xFF0000
GREEN  = 0x00FF00

# keep a small gap at the border of the display
GAP =  2

# --- application class   ----------------------------------------------------

class App:

  # --- constructor   --------------------------------------------------------

  def __init__(self):
    """ constructor """

    self._setup_hw()
    self._setup_hid()

    # helper for layout
    width  = self._display.width
    height = self._display.height
    self._map = {
      'NW': ((GAP,       GAP),        (0,0)),
      'W':  ((GAP,       height/2),   (0,0.5)),
      'SW': ((GAP,       height-GAP), (0,1)),
      'NE': ((width-GAP, GAP),        (1,0)),
      'E':  ((width-GAP, height/2),   (1,0.5)),
      'SE': ((width-GAP, height-GAP), (1,1))
    }

    self._secrets = SecretsManager()
    self._fields  = []
    self._group   = displayio.Group()
    self._background()
    self._create_fields()
    self._update_fields(self._secrets.current())
    self._display.show(self._group)

  # --- hardware-setup   ----------------------------------------------------

  def _setup_hw(self):
    """ setup hardware """

    displayio.release_displays()
    spi = busio.SPI(clock=PIN_CLK,MOSI=PIN_MOSI)
    bus = displayio.FourWire(spi,command=PIN_DC,chip_select=PIN_CS,
                             reset=PIN_RST)
    self._display = ST7735R(bus,width=TFT_WIDTH,height=TFT_HEIGHT,
                            colstart=28,rowstart=0,invert=True,
                            rotation=TFT_ROTATE,bgr=TFT_BGR)

    keys = keypad.Keys([PIN_USER,PIN_PW,PIN_UP,PIN_DOWN],
                       value_when_pressed=False,pull=True,
                       interval=0.1,max_events=4)
    self._key_events = keys.events
    self._key_callbacks = [
      self._on_user,self._on_pw,self._on_up,self._on_down
    ]

  # --- HID-setup   ----------------------------------------------------------

  def _setup_hid(self):
    """ setup HID-keyboard """

    keyboard       = Keyboard(usb_hid.devices)
    self._keyboard = KeyboardLayout(keyboard)

  # --- create background   --------------------------------------------------

  def _background(self):
    """ all black background """

    palette    = displayio.Palette(1)
    palette[0] = BLACK
    background = vectorio.Rectangle(pixel_shader=palette,
                                    width=self._display.width,
                                    height=self._display.height+4, x=0, y=0)
    self._group.append(background)

  # --- create text at given location   --------------------------------------

  def _create_text(self,pos,color,text):
    """ create text at given location """

    t = label.Label(FONT,text=text,color=color,
                    anchor_point=self._map[pos][1])
    t.anchored_position = self._map[pos][0]
    self._group.append(t)
    return t

  # --- create text-fields   -------------------------------------------------

  def _create_fields(self):
    """ create text fields for site, user, pw """

    colors = [WHITE,RED,GREEN]
    pos    = ['NW','W','SW']
    for i in range(3):
      field = self._create_text(pos[i],colors[i],"xxxxxxxxxxxxxxxxxx")
      self._fields.append(field)

  # --- update field contents   ----------------------------------------------

  def _update_fields(self,item):
    """ update field contents """

    for i in range(3):
      self._fields[i].text = item[i]

  # --- callback for user-key   ----------------------------------------------

  def _on_user(self):
    """ send username via HID """

    self._keyboard.write(self._secrets.current()[1])

  # --- callback for pw-key   ------------------------------------------------

  def _on_pw(self):
    """ send pw via HID """

    self._keyboard.write(self._secrets.current()[2])

  # --- callback for up-key   ------------------------------------------------

  def _on_up(self):
    """ show previous entry """

    self._update_fields(self._secrets.prev())

  # --- callback for down-key   ----------------------------------------------

  def _on_down(self):
    """ show next entry """

    self._update_fields(self._secrets.next())

  # --- main event loop   ----------------------------------------------------

  def run(self):
    """ main event loop """

    while True:
      event = self._key_events.get()
      if event and event.pressed:
        self._key_callbacks[event.key_number]()

# --- main-program   ---------------------------------------------------------

app = App()
app.run()
