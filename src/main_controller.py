# src/main_controller.py

from src.data_controller import DataController
from src.gcode_printer_controller import GCodePrinterController
from src.arduino_controller import ArduinoController
import time
from src.coords import CoordSystem

class MainController:
    def __init__(self, ui):
        self.ui = ui
        self.gcode_port = None
        self.arduino_port = None
        self.printer_controller = None
        self.arduino_controller = None
        
        self.data_controller = DataController()
        self.data_controller.initialize_db()
        
        self.coords = CoordSystem(mag_factor=4)      # <── NEW

        # Use raw coordinates without mag_factor multiplication
        self.slide_centers_raw = [
            (84.93, 36.40),
            (27.03, 36.40),
            (51.46, 91.20),
        ]
        # Store custom stimulation points (initially same as slide centers)
        self.custom_stimulation_points = self.slide_centers_raw.copy()

    def get_display_coordinates(self, x, y):
        """Convert raw coordinates to display coordinates."""
        return (x * self.mag_factor, y * self.mag_factor)

    def get_cnc_coordinates(self, x, y):
        """Convert raw coordinates to CNC machine coordinates."""
        # First convert to display coordinates
        display_x, display_y = self.get_display_coordinates(x, y)
        # Then transform to CNC coordinates (swap and divide by mag_factor)
        x_cnc = display_y / self.mag_factor
        y_cnc = display_x / self.mag_factor
        return x_cnc, y_cnc

    def get_raw_coordinates(self, display_x, display_y):
        """Convert display coordinates back to raw coordinates."""
        return (display_y / self.mag_factor, display_x / self.mag_factor)

    def update_stimulation_point(self, well_index, x, y):
        """Update a stimulation point and synchronize with PlateGrid."""
        self.custom_stimulation_points[well_index] = (x, y)
        if hasattr(self.ui, 'plate_grid'):
            self.ui.plate_grid.update_stimulation_point(well_index, x, y)

    def get_stimulation_points(self):
        """Get all stimulation points in display coordinates."""
        return [self.get_display_coordinates(x, y) for x, y in self.custom_stimulation_points]

    def get_slide_centers(self):
        """Get all slide centers in display coordinates."""
        return [self.get_display_coordinates(x, y) for x, y in self.slide_centers]

    def set_gcode_port(self, port):
        """Set the G-code printer port and initialize controller."""
        try:
            if self.printer_controller:
                self.printer_controller.close()
            self.gcode_port = port
            self.printer_controller = GCodePrinterController(port=self.gcode_port)
            if not self.printer_controller.connect():
                raise Exception("Failed to connect to G-code printer")
            self.log_message("G-code printer connected successfully")
        except Exception as e:
            self.log_message(f"Error setting G-code port: {e}")
            self.printer_controller = None
            raise

    def set_arduino_port(self, port):
        """Set the Arduino port and initialize controller."""
        try:
            if self.arduino_controller:
                self.arduino_controller.close()
            self.arduino_port = port
            self.arduino_controller = ArduinoController(port=self.arduino_port)
            if not self.arduino_controller.connect():
                raise Exception("Failed to connect to Arduino")
            self.log_message("Arduino connected successfully")
        except Exception as e:
            self.log_message(f"Error setting Arduino port: {e}")
            self.arduino_controller = None
            raise

    def test_cnc_connection(self):
        """Test the connection to the CNC by sending a test command."""
        if not self.printer_controller:
            self.log_message("CNC port not set. Please select a port.")
            return False

        try:
            self.log_message("Sending test command to CNC...")
            # Send a small movement command
            self.printer_controller.init_printer()
            self.printer_controller.wait_for_move_completion()
            self.printer_controller.move_to(50, 50)
            self.printer_controller.wait_for_move_completion()
            self.printer_controller.move_to(10, 50)
            self.log_message("CNC test successful.")
            return True
        except Exception as e:
            self.log_message(f"Error testing CNC connection: {e}")
            return False

    def test_arduino_connection(self):
        """Test the connection to the Arduino."""
        if not self.arduino_controller:
            self.log_message("Arduino port not set. Please select a port.")
            return False

        try:
            self.log_message("Sending test command to Arduino...")
            if self.arduino_controller.test_connection():
                self.log_message("Arduino test successful.")
                return True
            else:
                self.log_message("No response from Arduino. Check connection.")
                return False
        except Exception as e:
            self.log_message(f"Error testing Arduino connection: {e}")
            return False

    def execute_sequence(self):
        """Execute the sequence of movements and laser activations."""
        if not self.printer_controller or not self.arduino_controller:
            message = "Error: Please select valid ports for both the G-code printer and Arduino."
            self.log_message(message)
            return False
        
        try:
            # Initialize the printer
            self.log_message("Initializing printer...")
            self.printer_controller.init_printer()
            self.printer_controller.wait_for_move_completion()
            self.log_message("Printer initialized successfully")
            
            # Get current laser settings from the plate grid
            if hasattr(self.ui, 'plate_grid'):
                intensity = self.ui.plate_grid.intensity_input.value()
                pulse_duration = self.ui.plate_grid.duration_input.value()
                frequency = self.ui.plate_grid.frequency_input.value()
            else:
                # Default values if plate grid is not available
                intensity = 1.2
                pulse_duration = 100
                frequency = 0.5

            # First, move to the initial position (well 1)
            first_center = self.slide_centers[0]
            x, y = first_center
            message = f"Moving to initial position (well 1): ({x}, {y})"
            self.log_message(message)

            # Move CNC to initial position and wait for completion
            self.printer_controller.move_to(x, y)
            self.log_message("Waiting for movement to complete...")
            self.printer_controller.wait_for_move_completion()
            self.log_message("Movement to well 1 completed")
            
            # Wait a moment to ensure stability
            self.log_message("Waiting for stability...")
            time.sleep(2)
            self.log_message("Starting recipe execution at well 1")

            # Move through each position
            for i, center in enumerate(self.slide_centers):
                if i > 0:  # Skip first position as we're already there
                    x, y = center
                    message = f"Moving to position {i+1}: ({x}, {y})"
                    self.log_message(message)

                    # Move CNC to position and wait for completion
                    self.printer_controller.move_to(x, y)
                    self.log_message(f"Waiting for movement to position {i+1} to complete...")
                    self.printer_controller.wait_for_move_completion()
                    self.log_message(f"Movement to position {i+1} completed")

                # Activate laser with current settings
                message = f"Activating laser at position {i+1}..."
                self.log_message(message)

                try:
                    # Send recipe command to Arduino
                    self.arduino_controller.send_recipe_command(
                        intensity=intensity,
                        pulse_duration=pulse_duration,
                        frequency=frequency,
                        on_time=pulse_duration
                    )
                    
                    # Wait for recipe completion
                    response = self.arduino_controller.await_response("DONE", timeout=65)  # 60s max + 5s buffer
                    if not response:
                        raise Exception("Recipe execution did not complete (DONE not received)")
                    
                    message = f"Laser activation completed at position {i+1}"
                    self.log_message(message)
                    
                except Exception as e:
                    message = f"Error at position {i+1}: {str(e)}"
                    self.log_message(message)
                    raise

                # Wait a bit before moving to next position
                time.sleep(1)

            message = "Sequence completed successfully"
            self.log_message(message)
            return True

        except Exception as e:
            message = f"Error in sequence execution: {str(e)}"
            self.log_message(message)
            return False

    def emergency_stop(self):
        """Handle emergency stop by stopping all operations."""
        self.log_message("Emergency stop triggered!")
        try:
            if self.printer_controller:
                self.printer_controller.send_gcode("M112")  # Emergency stop command
            if self.arduino_controller:
                self.arduino_controller.ser.write(b'STOP\n')  # Stop command for Arduino
        except Exception as e:
            self.log_message(f"Error during emergency stop: {e}")

    def close_connections(self):
        """Close all connections and cleanup resources."""
        try:
            if self.printer_controller:
                self.printer_controller.close()
            if self.arduino_controller:
                self.arduino_controller.close()
            self.log_message("All connections closed successfully.")
        except Exception as e:
            self.log_message(f"Error closing connections: {e}")

    def log_message(self, message):
        """Log a message to the UI."""
        if hasattr(self.ui, 'log_message'):
            self.ui.log_message(message)
        print(message)  # Also print to console
