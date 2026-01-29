from machine import Pin
import time


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
