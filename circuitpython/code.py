import board
import terminalio
import busio as io

import rotaryio
import time
import displayio

import adafruit_displayio_ssd1306
from digitalio import DigitalInOut, Direction, Pull
from adafruit_display_text import label
from i2cdisplaybus import I2CDisplayBus

import usb_hid
from adafruit_hid.keyboard import Keyboard
from adafruit_hid.keycode import Keycode
from collections import OrderedDict

    ####################
    # DICTIONARY STUFF #
    ####################

#ninekey is seqential rows from left to right
buttons = OrderedDict([ #Dictionary of pins to keys. Edit this for custom boards. 17 entries
    ('ninekey_1', DigitalInOut(board.GP17)),
    ('ninekey_2', DigitalInOut(board.GP18)),
    ('ninekey_3', DigitalInOut(board.GP19)),
    ('ninekey_4', DigitalInOut(board.GP20)),
    ('ninekey_5', DigitalInOut(board.GP21)),
    ('ninekey_6', DigitalInOut(board.GP22)),
    ('ninekey_7', DigitalInOut(board.GP26)),
    ('ninekey_8', DigitalInOut(board.GP27)),
    ('ninekey_9', DigitalInOut(board.GP28)),
    ('rotencode_a_3', DigitalInOut(board.GP13)),
    ('rotencode_b_3', DigitalInOut(board.GP10)),
    ('fiveway_1', DigitalInOut(board.GP9)),  # up
    ('fiveway_2', DigitalInOut(board.GP8)),  # left
    ('fiveway_3', DigitalInOut(board.GP7)),  # down
    ('fiveway_4', DigitalInOut(board.GP6)),  # right
    ('fiveway_5', DigitalInOut(board.GP3)),  # down
    ('modeswitch', DigitalInOut(board.GP16))
])

specialkeys = { #Dictionary of special keys. DO NOT EDIT
    '↑': Keycode.UP_ARROW, #Up
    '↓': Keycode.DOWN_ARROW, #Down
    '←': Keycode.LEFT_ARROW, #Left
    '→': Keycode.RIGHT_ARROW, #Right
    'Ω': Keycode.CONTROL, #Ctrl
    'Φ': Keycode.SHIFT, #Shift
    'Ψ': Keycode.ALT, #Alt
    'λ': Keycode.SPACE, #Space
    '⊤': 1, #Scroll up
    '⊥':1, #Scroll down
    '⊢': 1, #Scroll left
    '⊣': 1, #Scroll right
    '1': Keycode.KEYPAD_ONE,#KEYPAD_ONE
    '2': Keycode.KEYPAD_TWO,#KEYPAD_TWO
    '3': Keycode.KEYPAD_THREE,#KEYPAD_THREE
    '4': Keycode.KEYPAD_FOUR,#KEYPAD_FOUR
    '5': Keycode.KEYPAD_FIVE,#KEYPAD_FIVE
    '6': Keycode.KEYPAD_SIX,#KEYPAD_SIX
    '7': Keycode.KEYPAD_SEVEN,#KEYPAD_SEVEN
    '8': Keycode.KEYPAD_EIGHT,#KEYPAD_EIGHT
    '9': Keycode.KEYPAD_NINE,#KEYPAD_NINE
    '0': Keycode.KEYPAD_ZERO,#KEYPAD_ZERO
    '[': Keycode.LEFT_BRACKET,
    ']': Keycode.RIGHT_BRACKET,
    '+': Keycode.EQUALS,
    '-': Keycode.MINUS,
    ';': Keycode.SEMICOLON,
    ',': Keycode.COMMA,
    '.': Keycode.PERIOD,
    '/': Keycode.FORWARD_SLASH,
    'Δ': Keycode.ENTER,
}
# add a ß to denote that key must be held
# add a Σ to denote macro- keys will be pressed in sequence rather than all at once
# add a ξ to denote alternate key (TO DO)
modes = [ #Mode Declaration
#             1    2   3    4   5   6   7   8  9 r1 r2  5u   5l   5d   5r   5c  ms  r1l  r1r r2l r2r
 ["DCS",     "Δ", "-", "+","", "1","6","7","","","","", "ß;", "ß,", "ß.", "ß/", "", "", "",  "", "", ""],
 ["Rebelle","Ωz","ΩΦz","Ωs","Φß","e","b","λß","xß","yß","a","a","a","a","a","a","a","a","[","]","+","-"],
 ["Blender","b"],
 ["Clip Studio","b"],
 ["HellDivers 2","Σ↑↓→↑","Σ↓↓↑→","Σ→→↓←→↓","Σ↓←↓↑→","a","a"] #↑↓←→
]

    ######################
    #INITIALIZATION STUFF#
    ######################

displayio.release_displays()
i2c = io.I2C(board.GP5, board.GP4) # update to the i2c pins of your display
display_bus = I2CDisplayBus(i2c, device_address=0x3C)
WIDTH = 128
HEIGHT = 32  # Change to 64 if needed
BORDER = 1 #border around text
display = adafruit_displayio_ssd1306.SSD1306(display_bus, width=WIDTH, height=HEIGHT, rotation=180)

kbd = Keyboard(usb_hid.devices) #declare we r a keyboard

# Make the display context
splash = displayio.Group()
display.root_group = splash
color_bitmap = displayio.Bitmap(WIDTH, HEIGHT, 1)
color_palette = displayio.Palette(1)
color_palette[0] = 0xFFFFFF  # White
bg_sprite = displayio.TileGrid(color_bitmap, pixel_shader=color_palette, x=0, y=0)
splash.append(bg_sprite)

# Draw a smaller inner rectangle
inner_bitmap = displayio.Bitmap(WIDTH - BORDER * 2, HEIGHT - BORDER * 2, 1)
inner_palette = displayio.Palette(1)
inner_palette[0] = 0x000000  # Black
inner_sprite = displayio.TileGrid(
    inner_bitmap, pixel_shader=inner_palette, x=BORDER, y=BORDER
)
splash.append(inner_sprite)

#screen bullshit
def changetext(inputtext):
    labels_to_remove = []
    for item in splash:
        if isinstance(item, label.Label):
            labels_to_remove.append(item)
    for label_to_remove in labels_to_remove:
        splash.remove(label_to_remove)
    text = inputtext
    text_area = label.Label(

        terminalio.FONT, text=text, color=0xFFFFFF, x=28, y=HEIGHT // 2 - 1

    )
    splash.append(text_area)

modeval = 0
mode = modes[modeval][0]

for button_name, button in buttons.items():
    button.direction = Direction.INPUT
    button.pull = Pull.UP
encoder = rotaryio.IncrementalEncoder(board.GP15, board.GP14)
encoder2 = rotaryio.IncrementalEncoder(board.GP12, board.GP11)
last_position = -1337
last_position2 = -1337

# Dictionary to keep track of button states for debounce
button_states = {button_name: False for button_name in buttons}

time_since_last_input = 0

def outputs(s):
    listofinputs = []
    ismacro = False
    ishold = False
    for char in s:
        if char in specialkeys:
            #add scrollwheel, mouse cursor, and mouse click functionality
            listofinputs.append(specialkeys[char])
        else:
            if char == "Σ": #special key: denotes macros
                ismacro = True
            if char == "ß": #special key: denotes that sequence must be held down
                ishold = True
            else:
                keycode = getattr(Keycode, char.upper(), None) #converts every key to its keycode
                if keycode is not None:
                    listofinputs.append(keycode)
    if not ismacro:
        print(listofinputs)
        if ishold:
            while button.value == False:
                kbd.press(*listofinputs)
        kbd.release_all()
        kbd.send(*listofinputs)
    if ismacro:
        print(listofinputs)
        #if mode == "HellDivers 2":
            #kbd.send(Keycode.CONTROL)
        #    pass
        for char in listofinputs:
            print(char)
            kbd.send(char)
            time.sleep(0.5) #lower = faster macros :-)
        #kbd.send(Keycode.CONTROL)

    #########################
    #CONTINUOUS POLLING LOOP#
    ###################b######

while True:
    position = encoder.position
    position2 = encoder2.position
    time_since_last_input += 1
    if last_position is -1337 or position != last_position: #code for first rotary encoder
        if last_position > position:
            changetext("1NEG")
            outputs(modes[modeval][18])
            time_since_last_input = 0
        else:
            changetext("1POS")
            outputs(modes[modeval][19])
            time_since_last_input = 0
    last_position = position

    if last_position2 is None or position2 != last_position2: #code for second rotary encoder
        if last_position2 > position2:
            changetext("2NEG")
            outputs(modes[modeval][20])
            time_since_last_input = 0
        else:
            changetext("2POS")
            outputs(modes[modeval][21])
            time_since_last_input = 0
    last_position2 = position2

    for button_name, button in buttons.items():
        button_state = button.value # Read the current state of the button
        if button_state != button_states[button_name]: # Check if the button state has changed
            button_states[button_name] = button_state# Update the button state in the dictionary
            if not button_state: # Check if the button is pressed (state is False)
                if button_name == "modeswitch":
                    if time_since_last_input < 25:
                        modeval += 1
                        if modeval > len(modes)-1:
                            modeval = 0
                        mode = modes[modeval][0]
                        print(mode)
                    time_since_last_input = 0
                    changetext(mode)
                else:
                    time_since_last_input = 0
                    changetext(button_name)
                    keyindex = (list(buttons).index(button_name))
                    keyindex+=1
                    if keyindex < len(modes[modeval]):
                        outputs(modes[modeval][keyindex])
    if time_since_last_input > 100:
        splash.hidden = True
        time.sleep(0.1)
    else:
        splash.hidden = False
        time.sleep(0.01) #lower = faster :-)
