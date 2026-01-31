from machine import Pin, PWM
import time
import struct
import array

print('Debounce v0.7 - WAV Playback with Timing')

class WavPlayer:
    def __init__(self, pin_num):
        self.pin_num = pin_num
        self.pwm = None
        
    def play_wav(self, filename):
        """Play a WAV file (blocking). Assumes 16-bit mono."""
        with open(filename, 'rb') as f:
            # Skip WAV header (44 bytes standard)
            f.seek(44)
            
            # Read and play samples in chunks
            while True:
                chunk = f.read(512)  # Read 256 samples (512 bytes)
                if not chunk:
                    break
                
                # Convert to array of signed 16-bit integers
                samples = array.array('h', chunk)
                
                # Play each sample with timing
                for i, sample in enumerate(samples):
                    duty = sample + 32768
                    self.pwm.duty_u16(duty)
                    
                    # Timing with periodic yields to keep serial alive
                    # if i % 50 == 0:  # Every 50 samples
                    #     time.sleep_ms()  # 2ms sleep allows serial to work
                    # else:
                    time.sleep_us(16)  # Normal per-sample delay
    
    def play_files(self, filenames):
        """Play multiple WAV files in sequence."""
        # Initialize PWM once for all files
        self.pwm = PWM(Pin(self.pin_num))
        self.pwm.freq(22050)
        
        for filename in filenames:
            print(f"Playing: {filename}")
            self.play_wav(filename)
        
        # Shut down PWM after all files played
        self.pwm.deinit()
        self.pwm = None

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

# Initialize audio player
player = WavPlayer(21)  # GP21 (physical pin 27)

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
    else:
        # Normal mode - speak the time
        print("Speaking time...")
        files = ['word_half.wav', 'word_past.wav']  # Test files
        player.play_files(files)

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