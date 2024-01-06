from machine import Pin, I2C
import utime
from esp32_gpio_lcd import GpioLcd

# Initialize LCD (replace pin numbers with your setup)
lcd = GpioLcd(rs_pin=Pin(16), enable_pin=Pin(17), d4_pin=Pin(18),
              d5_pin=Pin(19), d6_pin=Pin(20), d7_pin=Pin(21),
              num_lines=2, num_columns=16)

# Create a map between keypad buttons and characters
matrix_keys = [['1', '2', '3', 'A'],
               ['4', '5', '6', 'B'],
               ['7', '8', '9', 'C'],
               ['*', '0', '#', 'D']]

# PINs according to schematic - Change the pins to match with your connections
keypad_rows = [9,8,7,6]
keypad_columns = [5,4,3,2]

# Create two empty lists to set up pins ( Rows output and columns input )
col_pins = []
row_pins = []

# red button
button = Pin(28, Pin.IN, Pin.PULL_UP)  # Assuming GPIO10 is used
last_button_press_time = 0


# Loop to assign GPIO pins and setup input and outputs
for x in range(0,4):
    row_pins.append(Pin(keypad_rows[x], Pin.OUT))
    row_pins[x].value(1)
    col_pins.append(Pin(keypad_columns[x], Pin.IN, Pin.PULL_DOWN))
    col_pins[x].value(0)
# buzzer
buzzer = Pin(13, Pin.OUT)

# leds
rled = Pin(14, Pin.OUT)
wled = Pin(15, Pin.OUT)

# game vars
gameOver = False
codelength = 6
remaining_time = 40
waitEnd = 0


countdown_duration = 40000

beep_duration = 100  # duration in milliseconds
flash_duration = 100  # duration in milliseconds
last_beep_time = utime.ticks_ms()
last_flash_time = utime.ticks_ms()

delay1 = 0
delay1starttime = 0
    
print("Please enter a key from the keypad")
def scan_keypad():  
    for row in range(4):
        for col in range(4):
            row_pins[row].high()
            key = None
            
            if col_pins[col].value() == 1:
                print("You have pressed:", matrix_keys[row][col])
                key_press = matrix_keys[row][col]
                return matrix_keys[row][col]
                utime.sleep(0.3)
                    
        row_pins[row].low()

def non_blocking_delay(start_time, duration):
    return utime.ticks_diff(utime.ticks_ms(), start_time) < duration

def update_buzzer_and_leds(remaining_time, last_update_time):
    on_duration = 1000  # Default duration in milliseconds
    off_duration = 1000 # Default duration in milliseconds

    if remaining_time <= 20:
        on_duration = 500
        off_duration = 500
    if remaining_time <= 10:
        on_duration = 250
        off_duration = 250
    if remaining_time <= 5:
        on_duration = 100
        off_duration = 125

    current_time = utime.ticks_ms()

    if non_blocking_delay(last_update_time, on_duration):
        buzzer.value(1)
        rled.value(1)
        if remaining_time <= 2:
            wled.value(1)
    elif non_blocking_delay(last_update_time, on_duration + off_duration):
        buzzer.value(0)
        rled.value(0)
        wled.value(0)
    else:
        return current_time  # Update the last_update_time

    return last_update_time

def boom(start_time):
    end_time = start_time + 3000  # 3000 milliseconds = 3 seconds
    while utime.ticks_diff(utime.ticks_ms(), start_time) < 3000:
        current_time = utime.ticks_ms()
        
        # Toggle LEDs rapidly
        if utime.ticks_diff(current_time, start_time) % 100 < 50:
            rled.value(1)
            wled.value(0)
        else:
            rled.value(0)
            wled.value(1)

        # Keep the buzzer on
        buzzer.value(1)

    # Turn off LEDs and buzzer after 3 seconds
    rled.value(0)
    wled.value(0)
    buzzer.value(0)
    
def check_button_press():
    global last_button_press_time
    last_press_time = last_button_press_time
    if button.value() == 0:  # Button is pressed
        if last_press_time == 0:
            last_press_time = utime.ticks_ms()
        elif utime.ticks_diff(utime.ticks_ms(), last_press_time) >= 3000:
            last_button_press_time = 0
            return "restart"
    else:
        if last_press_time != 0:
            if utime.ticks_diff(utime.ticks_ms(), last_press_time) < 3000:
                last_button_press_time = 0
                return "activate"
            last_press_time = 0
    last_button_press_time = last_press_time    
    return None


def reset():
    global gameOver, remaining_time, waitEnd, beep_duration, flash_duration, last_beep_timem, last_flash_time, delay1, delay1starttime
    gameOver = False
    remaining_time = 40
    waitEnd = 0

    beep_duration = 100  # duration in milliseconds
    flash_duration = 100  # duration in milliseconds
    last_beep_time = utime.ticks_ms()
    last_flash_time = utime.ticks_ms()

    delay1 = 0
    delay1starttime = 0
    buzzer.value(0)
    rled.value(0)
    wled.value(0)

    

def gameloop():
    lcd.clear()
    lcd.putstr("Set Bomb Code:\n")
    last_update_time = utime.ticks_ms()
    lcd.move_to(0, 1)
    
    # Set the bomb code
    bomb_code = ''
    while len(bomb_code) < codelength:  # 6-digit bomb code
        if check_button_press() == "restart":
            buzzer.value(1)
            utime.sleep(2)
            buzzer.value(0)
            reset()
        key = scan_keypad()
        if key and key not in "ABCD*#":
            bomb_code += key
            lcd.putstr(key)
            utime.sleep_ms(500)
    lcd.clear()
    print(bomb_code)

    start_time = utime.ticks_ms()
    defuse_code = ''
    display_code = bomb_code  # Code displayed on the LCD
    lcd.move_to(0,0)
    lcd.putstr("Code: "+ str(display_code))

    while non_blocking_delay(start_time, countdown_duration):
        # handleing button input
        if check_button_press() == "restart":
            buzzer.value(1)
            utime.sleep(2)
            buzzer.value(0)
            reset()
        
        current_time = utime.ticks_diff(utime.ticks_ms(), start_time)
        remaining_time = 40 - current_time // 1000
        lcd.move_to(0, 1)
        lcd.putstr("Time: " + str(remaining_time) + " ")
        last_update_time = update_buzzer_and_leds(remaining_time, last_update_time)
        

        key = scan_keypad()
        if key and key not in "ABCD*#":
            if len(defuse_code) < len(bomb_code) and bomb_code[len(defuse_code)] == key:
                defuse_code += key
                # Update the display to hide one digit of the bomb code
                display_code = bomb_code[len(defuse_code):]
                lcd.move_to(0, 0)
                lcd.putstr('                ')
                lcd.move_to(0, 0)
                lcd.putstr("Code: "+ str(display_code))
            else:
                # If the wrong key was pressed, reset the defuse code
                defuse_code = ''
                display_code = bomb_code
                lcd.move_to(0, 0)
                lcd.putstr("Code: "+ str(display_code))

            if defuse_code == bomb_code:
                lcd.clear()
                lcd.putstr("  ! DEFUSED !")
                buzzer.value(0)
                rled.value(0)
                wled.value(0)
                break
            utime.sleep(0.3)

    if defuse_code != bomb_code:
        lcd.clear()
        lcd.putstr("    ! BOOM !")
        start_time = utime.ticks_ms()
        boom(start_time)
    


gameloop()
buzzer.value(1)
utime.sleep(2)
buzzer.value(0)

while True:
    if scan_keypad() == "#":
        buzzer.value(1)
        rled.value(1)
        wled.value(1)
        utime.sleep(2)
        buzzer.value(0)
        rled.value(0)
        wled.value(0)
        reset()
        gameloop()
    else:
        pass;by77w8e 