"""note: you have to run sudo pigpiod firat
"""
import pigpio
import time

# Define GPIO pins
LEFT_INPUT_PIN = 22
RIGHT_INPUT_PIN = 27

# NOTE: will have to uncomment some of these for the other two motors later
LEFT_DIR_PIN = 16
LEFT_SPEED_PIN = 19
# LEFT_DIR_PIN_2 = 12
# LEFT_SPEED_PIN_2 = 26

RIGHT_DIR_PIN = 18
RIGHT_SPEED_PIN = 13
# RIGHT_DIR_PIN_2 = 21
# RIGHT_SPEED_PIN_2 = 20

E_BRAKE_INPUT = 5
FAN_PIN = 25

# Initialize pigpio
pi = pigpio.pi()

if not pi.connected:
   print("Failed to connect to pigpio daemon.")
   exit()

# Set up direction pins
pi.set_mode(LEFT_DIR_PIN, pigpio.OUTPUT)
# pi.set_mode(LEFT_DIR_PIN_2, pigpio.OUTPUT)
pi.set_mode(RIGHT_DIR_PIN, pigpio.OUTPUT)
# pi.set_mode(RIGHT_DIR_PIN_2, pigpio.OUTPUT)
pi.set_mode(FAN_PIN, pigpio.OUTPUT)


# Set up PWM pins for speed
pi.set_PWM_frequency(LEFT_DIR_PIN, 100)  # Set PWM frequency to 100Hz
# pi.set_PWM_frequency(LEFT_DIR_PIN_2, 100)  # Set PWM frequency to 100Hz
pi.set_PWM_frequency(RIGHT_DIR_PIN, 100)  # Set PWM frequency to 100Hz
# pi.set_PWM_frequency(RIGHT_DIR_PIN_2, 100)  # Set PWM frequency to 100Hz

pi.set_PWM_dutycycle(LEFT_DIR_PIN, 0)  # Start with LED off
pi.set_PWM_dutycycle(RIGHT_DIR_PIN, 0) 

# Variable to store pulse width
# pulse_width_22 = 1500  # Default neutral position
pulse_width_right = 1500  # Default neutral position
pulse_width_left = 1500  # Default neutral position
pulse_width_brake = 1500
last_tick = {}

def pulse_callback(gpio, level, tick):
   """ Callback function to measure PWM pulse width. """
   global last_tick, pulse_width_left, pulse_width_right, pulse_width_brake
   if level == 1:  # Rising edge
      last_tick[gpio] = tick
   elif level == 0 and gpio in last_tick:  # Falling edge
      if gpio == LEFT_INPUT_PIN:
         pulse_width_left = pigpio.tickDiff(last_tick[gpio], tick)
      elif gpio == RIGHT_INPUT_PIN:
         pulse_width_right = pigpio.tickDiff(last_tick[gpio], tick)
      elif gpio == E_BRAKE_INPUT:
         pulse_width_brake = pigpio.tickDiff(last_tick[gpio], tick)

         
# Attach callback to measure PWM on pins 22 and 27 for both inputs
pi.callback(LEFT_INPUT_PIN, pigpio.EITHER_EDGE, pulse_callback)
pi.callback(RIGHT_INPUT_PIN, pigpio.EITHER_EDGE, pulse_callback)
pi.callback(E_BRAKE_INPUT, pigpio.EITHER_EDGE, pulse_callback)

try:
   left_speed=0
   right_speed=0
   pi.write(FAN_PIN,0)
   while True:
      # Control LEFT side
      if pulse_width_left > 1500:
         pi.write(LEFT_DIR_PIN, 1)  # Turn LED ON
         left_speed = max(0, min(255, int((pulse_width_left - 1500) * (255 / 500))))  # Scale 1500-2000 to 0-255
      else:
         pi.write(LEFT_DIR_PIN, 0)  # Turn LED OFF
         left_speed = max(0, min(255, int((1500 - pulse_width_left) * (255 / 500))))  # Scale 1500-1000 to 0-255
      # Control RIGHT side
      if pulse_width_right < 1500:
         pi.write(RIGHT_DIR_PIN, 1)  # Turn LED OFF
         right_speed = max(0, min(255, int((1500 - pulse_width_right) * (255 / 500))))  # Scale 1500-1000 to 0-255
      else:
         pi.write(RIGHT_DIR_PIN, 0)  # Turn LED ON
         right_speed = max(0, min(255, int((pulse_width_right - 1500) * (255 / 500))))  # Scale 1500-2000 to 0-255
      
      # control FAN
      if pulse_width_brake > 1700:
         pi.write(FAN_PIN,1)
      elif pulse_width_brake < 1700:
         pi.write(FAN_PIN,0)
         

      # Set PWM brightness for speed pins
      pi.set_PWM_dutycycle(LEFT_SPEED_PIN, left_speed)
      # pi.set_PWM_dutycycle(LEFT_SPEED_PIN_2, brightness)
      pi.set_PWM_dutycycle(RIGHT_SPEED_PIN, right_speed)
      # pi.set_PWM_dutycycle(RIGHT_SPEED_PIN_2, brightness)

      print(f"LEFT IN Pulse: {pulse_width_left} µs, LEFT DIR: {'ON' if pulse_width_left > 1500 else 'OFF'}, LEFT SPEED: {left_speed}")
      print(f"RIGHT IN Pulse: {pulse_width_right} µs, RIGHT DIR: {'OFF' if pulse_width_right > 1500 else 'ON'}, RIGHT SPEED: {right_speed}\n")
      
      time.sleep(0.1)  # Update every 100ms
except KeyboardInterrupt:
   print("Exiting program.")

finally:
   # make sure all motors are off
   pi.write(LEFT_DIR_PIN, 0) 
   # pi.write(LEFT_DIR_PIN_2, 0)  
   pi.write(RIGHT_DIR_PIN, 0) 
   # pi.write(RIGHT_DIR_PIN_2, 0) 
   
   
   pi.set_PWM_dutycycle(LEFT_SPEED_PIN, 0)  # Turn off PWM
   # pi.set_PWM_dutycycle(LEFT_SPEED_PIN_2, 0)  # Turn off PWM
   pi.set_PWM_dutycycle(RIGHT_SPEED_PIN, 0)  # Turn off PWM
   # pi.set_PWM_dutycycle(RIGHT_SPEED_PIN_2, 0)  # Turn off PWM
   
   
   pi.stop()  # Clean up pigpio connection
