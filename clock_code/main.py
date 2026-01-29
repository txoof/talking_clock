from machine import Pin
import time

print('Debounce v0.1 - Set Mode')

class DebounceButton:
    def __init__(self, pin_num, callback):
        self.pin = Pin(pin_num, Pin.IN, Pin.PULL_UP)
        self.callback = callback
        self.last_time = 0
        self.pin.irq(trigger=Pin.IRQ_FALLING, handler=self._handler)

    def _handler(self, pin):
        now = time.ticks_ms()
        if time.ticks_diff(now, self.last_time) > 50:
            self.last_time = now
            self.callback()

# State variables
hour = 0
minute = 0
set_mode = None  # None, 'hour', or 'minute'
hold_start = None
last_heartbeat = time.ticks_ms()

def check_hold():
    global set_mode, hold_start
    if hold_start and time.ticks_diff(time.ticks_ms(), hold_start) > 5000:
        if set_mode is None:
            set_mode = 'hour'
            print(f"enter set mode: hour (current: {hour})")
        hold_start = None

def button_plus_pressed():
    global hour, minute, hold_start
    if set_mode is None:
        hold_start = time.ticks_ms()
    elif set_mode == 'hour':
        hour = (hour + 1) % 24
        print(f"Hour: {hour}")
    elif set_mode == 'minute':
        minute = (minute + 1) % 60
        print(f"Minute: {minute}")

def button_minus_pressed():
    global hour, minute, hold_start
    if set_mode is None:
        hold_start = time.ticks_ms()
    elif set_mode == 'hour':
        hour = (hour - 1) % 24
        print(f"Hour: {hour}")
    elif set_mode == 'minute':
        minute = (minute - 1) % 60
        print(f"Minute: {minute}")

def button_speak_pressed():
    global set_mode
    if set_mode == 'hour':
        set_mode = 'minute'
        print(f"enter set mode: minute (current: {minute})")
    elif set_mode == 'minute':
        set_mode = None
        print(f"exit set mode - Time set to {hour:02d}:{minute:02d}")

button_plus = DebounceButton(2, button_plus_pressed)
button_minus = DebounceButton(5, button_minus_pressed)
button_speak = DebounceButton(8, button_speak_pressed)

print("Ready. Hold plus+minus for 5s to enter set mode.")
print(f"Current time: {hour:02d}:{minute:02d}")

while True:
    check_hold()
    
    # Non-blocking heartbeat every 5 seconds
    now = time.ticks_ms()
    if time.ticks_diff(now, last_heartbeat) > 5000:
        print(f"Heartbeat - Time: {hour:02d}:{minute:02d}, Mode: {set_mode}")
        last_heartbeat = now
    
    time.sleep(0.01)