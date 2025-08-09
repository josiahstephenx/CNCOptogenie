# src/gcode_printer_controller.py

import serial
import time
from serial import SerialException

class GCodePrinterController:
    def __init__(self, port, baud_rate=115200, speed=700, acceleration=150):
        self.port = port
        self.baud_rate = baud_rate
        self.speed = speed
        self.acceleration = acceleration
        self.ser = None
        self.connect()

    def connect(self):
        """Establish connection to G-code printer with proper error handling."""
        try:
            if self.ser and self.ser.is_open:
                self.ser.close()
            self.ser = serial.Serial(self.port, self.baud_rate, timeout=1)
            time.sleep(2)  # Wait for serial connection
            # Clear any pending data
            self.ser.reset_input_buffer()
            self.ser.reset_output_buffer()
            return True
        except SerialException as e:
            print(f"Error connecting to G-code printer: {e}")
            self.ser = None
            return False

    def send_gcode(self, command):
        """Send a G-code command to the printer."""
        if not self.ser or not self.ser.is_open:
            raise Exception("G-code printer not connected")

        try:
            command += '\n'
            self.ser.write(command.encode('ascii'))
            time.sleep(0.1)
        except SerialException as e:
            print(f"Serial error in send_gcode: {e}")
            self.reconnect()
            raise Exception(f"Serial communication error: {e}")

    def wait_for_move_completion(self, timeout=30):
        """Wait for the printer to finish the move with timeout."""
        if not self.ser or not self.ser.is_open:
            raise Exception("G-code printer not connected")

        try:
            # Clear any pending data
            while self.ser.in_waiting > 0:
                self.ser.read()

            # Send M400 to wait for moves to complete
            self.send_gcode("M400")
            
            # Wait for "ok" response
            start_time = time.time()
            while (time.time() - start_time) < timeout:
                if self.ser.in_waiting > 0:
                    response = self.ser.readline().decode('ascii').strip()
                    print(f"Printer response: {response}")
                    if response == "ok":
                        # Get current position
                        self.send_gcode("M114")
                        position = self.ser.readline().decode('ascii').strip()
                        print(f"Current position: {position}")
                        return True
                time.sleep(0.1)
            
            raise Exception("Move completion timeout")
        except SerialException as e:
            print(f"Serial error in wait_for_move_completion: {e}")
            self.reconnect()
            raise Exception(f"Serial communication error: {e}")

    def init_printer(self):
        """Initialize the printer with basic settings."""
        if not self.ser or not self.ser.is_open:
            raise Exception("G-code printer not connected")

        try:
            self.send_gcode("M201 X150 Y150 Z100")  # Set max acceleration
            self.send_gcode("M203 X100 Y100 Z30")   # Set max feedrate
            self.send_gcode("G28")                  # Home all axes
            self.send_gcode("G53")                  # Move machine coordinates
            self.send_gcode("G21")                  # Set units to mm
            self.send_gcode("M104 S18")             # Set temperature
            self.send_gcode("G90")                  # Set absolute positioning
            self.send_gcode(f"M204 P{self.acceleration}")
            return True
        except Exception as e:
            print(f"Error initializing printer: {e}")
            raise

    def move_to(self, x, y):
        """Move to specified coordinates."""
        if not self.ser or not self.ser.is_open:
            raise Exception("G-code printer not connected")

        try:
            self.send_gcode(f"G1 X{x} Y{y} F{self.speed}")
            self.wait_for_move_completion()
        except Exception as e:
            print(f"Error moving to position ({x}, {y}): {e}")
            raise

    def reconnect(self):
        """Attempt to reconnect to the G-code printer."""
        print("Attempting to reconnect to G-code printer...")
        if self.ser and self.ser.is_open:
            self.ser.close()
        time.sleep(1)  # Wait before reconnecting
        return self.connect()

    def close(self):
        """Close the serial connection."""
        if self.ser and self.ser.is_open:
            try:
                self.ser.close()
            except SerialException as e:
                print(f"Error closing G-code printer connection: {e}")
            finally:
                self.ser = None
