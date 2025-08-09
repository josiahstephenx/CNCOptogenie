import serial
import time

# Define the COM ports for the G-code printer and Arduino
gcode_port = '/dev/cu.usbserial-1130'  # Change to the correct port for your G-code printer
arduino_port = '/dev/cu.usbmodem11201'  # Port for Arduino
baud_rate = 115200
speed = 700
acceleration = 150
slideCentres = [(23, 9), (75, 42), (22, 67)]

# Open the serial connections
try:
    ser_gcode = serial.Serial(gcode_port, baud_rate, timeout=1)
    ser_arduino = serial.Serial(arduino_port, baud_rate, timeout=1)
except serial.SerialException as e:
    print(f"Error opening serial port: {e}")
    # sys.exit()

# Wait for the serial connections to be established
time.sleep(2)

# Define a function to send GCODE commands to the printer
def send_gcode(command):
    command += '\n'  # Add newline character '\n' to the end of the command
    ser_gcode.write(command.encode('ascii'))  # Encode the command as ASCII and send it over serial
    time.sleep(0.1)  # Wait for the command to be executed

# Define a function to wait for the printer to finish the move
def wait_for_move_completion():
    send_gcode("M400")
    while ser_gcode.in_waiting > 0:
        ser_gcode.read()
    send_gcode("M400")  # Wait for current moves to finish
    while True:
        if ser_gcode.in_waiting > 0:
            response = ser_gcode.readline().decode('ascii').strip()
            print("WAIT" + str(response))
            if response == "ok":
                break
    send_gcode("M114")
    response = ser_gcode.readline().decode('ascii').strip()
    print("POS" + str(response))

# Initialization - need to read back from serial port outstanding responses
def initPrinter():
    send_gcode("M201 X150 Y150 Z100")  # Set max acceleration for X, Y, Z axes
    send_gcode("M203 X100 Y100 Z30")   # Set max feedrate for X, Y, Z axes
    send_gcode("G28")                  # Home all axes
    send_gcode("G53")                  # Move machine coordinates
    send_gcode("G21")                  # Move in 'mm'
    send_gcode("M104 S18")             # Reset Calibration temperature to 18°C
    send_gcode("G90")                   # Set Absolute positioning
    send_gcode("M204 P" + str(acceleration))
    

def moveTo(x, y):
    send_gcode("G1 X" + str(x) + " Y" + str(y) + " F" + str(speed))
    wait_for_move_completion()  # Wait for the move to complete
    send_gcode("G1 X" + str(x) + " Y" + str(y) + " F" + str(speed))
    wait_for_move_completion()  # Wait for the move to complete

# Initialize the printer
initPrinter()

# Move to each slide center sequentially with a 5-second delay between movements
for center in slideCentres:
    moveTo(center[0], center[1])
    print(f"Moved to ({center[0]}, {center[1]})")

    # Send command to start laser on Arduino after reaching each slide center
    print("Sending S command to Arduino...")
    ser_arduino.write(b'S\n')  # Send command to Arduino
    while True:
        if ser_arduino.in_waiting > 0:
            response = ser_arduino.readline().decode('ascii').strip()
            print("WAIT" + str(response))
            if response == "finished":
                break
    time.sleep(0.5)  # Add a delay to give Arduino time to read the command
    time.sleep(5)  # 5-second delay at each position

# Close the serial connections
ser_gcode.close()
ser_arduino.close()