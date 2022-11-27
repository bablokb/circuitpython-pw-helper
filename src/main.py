# ----------------------------------------------------------------------------
# main.py: main driver program
#
# Display: Waveshare Pico-0.96 LCD-display with joystick and two buttons
#          https://www.waveshare.com/wiki/Pico-LCD-0.96
#
# Other hardware requires other pins and probably a different display-driver
#
# The program has two modes: an initial slideshow-mode and the final
# keys-mode (HID). The intial mode is used to obfuscate the main purpose
# of the gadget. If the user presses the enter-button during display
# of a predefined image, the device switches from slideshow to keys-mode.
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

# application library
from SecretsManager import SecretsManager as SecretsManager

# --- configuration   --------------------------------------------------------

IMAGES    = ['image00.bmp','image01.bmp','image02.bmp',
             'image03.bmp','image04.bmp']
KEY_IMAGE = 2

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
PIN_ENTER = board.GP3

# unused pins
PIN_LEFT  = board.GP16
PIN_RIGHT = board.GP20

# fonts and colors
FONT            = bitmap_font.load_font("fonts/DejaVuSansMono-Bold-24.bdf")
BG_COLOR        = 0x000000      # black
SITE_COLOR      = 0xFFFFFF      # white
USERNAME_COLOR  = 0xFF0000      # red
PASSWORD_COLOR  = 0x00FF00      # green

# keep a small gap at the border of the display
GAP =  2

# --- application class   ----------------------------------------------------

class App:

  # --- constructor   --------------------------------------------------------

  def __init__(self):
    """ constructor """

    self._setup_hw()

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
    self._img_nr  = 0
    self._group   = displayio.Group()
    self._update_image()

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

    keys = keypad.Keys([PIN_USER,PIN_PW,PIN_UP,PIN_DOWN,PIN_ENTER],
                       value_when_pressed=False,pull=True,
                       interval=0.1,max_events=4)
    self._key_events = keys.events
    self._switch_on = KEY_IMAGE
    self._key_callbacks = [
      self._on_img_prev,self._on_img_next,self._on_img_prev,
      self._on_img_next,self._on_img_select
    ]

  # --- HID-setup   ----------------------------------------------------------

  def _setup_hid(self):
    """ setup HID-keyboard """

    # HID-libraries
    import usb_hid
    from adafruit_hid.keyboard  import Keyboard
    from keyboard_layout_win_de import KeyboardLayout

    keyboard       = Keyboard(usb_hid.devices)
    self._keyboard = KeyboardLayout(keyboard)

  # --- switch to keys-mode   ------------------------------------------------

  def _switch_mode(self):
    """ switch to keys-mode """

    self._setup_hid()
    self._key_callbacks = [
      self._on_user,self._on_pw,self._on_up,self._on_down,self._noop
    ]
    del self._group[0]
    self._background()
    self._create_fields()
    self._update_fields(self._secrets.current())

  # --- create background   --------------------------------------------------

  def _background(self):
    """ all bg_color background """

    palette    = displayio.Palette(1)
    palette[0] = BG_COLOR
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

    colors = [SITE_COLOR,USERNAME_COLOR,PASSWORD_COLOR]
    pos    = ['NW','W','SW']
    for i in range(3):
      field = self._create_text(pos[i],colors[i],"xxxxxxxxxxxxxxxxxx")
      self._fields.append(field)

  # --- update field contents   ----------------------------------------------

  def _update_fields(self,item):
    """ update field contents """

    for i in range(3):
      self._fields[i].text = item[i]

  # --- update image on the screen   -----------------------------------------

  def _update_image(self):
    img_file = open(IMAGES[self._img_nr], "rb")
    bmp  = displayio.OnDiskBitmap(img_file)
    tile = displayio.TileGrid(bmp,pixel_shader=displayio.ColorConverter())

    if len(self._group) == 1:
      del self._group[0]
    self._group.append(tile)
    self._display.show(self._group)
    self._display.refresh()

  # --- empty callback   -----------------------------------------------------

  def _noop(self):
    """ empty callback """
    pass

  # --- callback for enter-key   ---------------------------------------------

  def _on_img_select(self):
    """ select image and switch mode """

    if self._img_nr == self._switch_on:
      self._switch_mode()
    else:
      # we allow no error (this effectively disables a mode-switch)
      KEY_IMAGE = -1

  # --- callback for user-key/up-key in slideshow-mode   ---------------------

  def _on_img_prev(self):
    """ select previous image """

    if self._img_nr == 0:
      self._img_nr = len(IMAGES) - 1
    else:
      self._img_nr = self._img_nr - 1
    self._update_image()

  # --- callback for pw-key/down-key in slideshow-mode   ---------------------

  def _on_img_next(self):
    """ select next image """

    self._img_nr = (self._img_nr + 1) % len(IMAGES)
    self._update_image()

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
