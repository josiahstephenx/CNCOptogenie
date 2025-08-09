from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QLineEdit,
    QTabWidget,
    QDoubleSpinBox,
)
from PySide6.QtCore import Qt, QTimer, QObject, Signal
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
import matplotlib.pyplot as plt
import numpy as np

from src.coords import CoordSystem


class PlateGridSignalEmitter(QObject):
    log_message_signal = Signal(str)

    def __init__(self):
        super().__init__()



class PlateGrid(QWidget):

    def __init__(self, main_controller):

        super().__init__()



        self.coords: CoordSystem = main_controller.coords
        mag_factor = self.coords.mag_factor
        self.laser_step = 1.0             # 5 mm in real units
        # single source-of-truth laser position (raw millimetres)
        self.laser_raw = list(main_controller.slide_centers_raw[0])


        self.main_controller = main_controller
        self.signal_emitter = PlateGridSignalEmitter()

        # Platform and well sizes
        self.platform_size = (
            127 * mag_factor,
            118 * mag_factor,
        )  # Width x Height of the holder


        self.well_centers_raw = [
            (84.93, 36.40),
            (27.03, 36.40),
            (51.46, 91.20)]
        
        self.well_size = 53 * mag_factor
        self.circle_radius = 10 * mag_factor

        self.custom_stimulation_points = self.well_centers_raw.copy()

        main_layout = QHBoxLayout()

        # Plate Layout on the left
        plate_layout = QVBoxLayout()

        # Title
        title = QLabel("Plate Layout")
        title.setStyleSheet("font-weight: bold; font-size: 16px;")
        title.setAlignment(Qt.AlignCenter)
        plate_layout.addWidget(title)

        # Initialize matplotlib figure and canvas
        self.figure, self.ax = plt.subplots(
            figsize=(self.platform_size[0] / 50, self.platform_size[1] / 50)
        )
        self.canvas = FigureCanvas(self.figure)

        # Remove background color of figure, but set platform background to white
        self.figure.patch.set_alpha(0)
        self.ax.set_facecolor("none")

        plate_layout.addWidget(self.canvas)

        main_layout.addLayout(plate_layout)

        # Tab Widget for Controls and Laser Parameters
        tab_widget = QTabWidget()
        control_tab = QWidget()
        laser_param_tab = QWidget()

        # Control Tab Layout
        control_layout = QVBoxLayout(control_tab)

        # Calibration Layout
        calibration_layout = QVBoxLayout()
        calibration_layout.addWidget(QLabel("Well Calibration Values"))

        # List to store QLineEdit widgets for each well's stimulation point display
        self.well_calibration_entries = []

        for i in range(3):
            # Label and text box for each well's stimulation point
            label = QLabel(f"Well {i + 1} Stimulation Point:")
            entry = QLineEdit(f"{self.custom_stimulation_points[i]}")
            entry.setReadOnly(True)  # Make it read-only by default
            calibration_layout.addWidget(label)
            calibration_layout.addWidget(entry)
            self.well_calibration_entries.append(entry)

            # Button to set well's stimulation point to current laser position
            set_button = QPushButton(f"Set Well {i + 1} to Current Position")
            set_button.clicked.connect(
                lambda _, index=i: self.set_stimulation_point(index)
            )
            calibration_layout.addWidget(set_button)

        self.laser_x, self.laser_y = self.well_centers_raw[0]
        self.laser_position, = self.ax.plot([], [], 'ro', markersize=13, label="Laser Position")
        self.update_laser_position(self.laser_x, self.laser_y)

        control_layout.addLayout(calibration_layout)

        # Add control buttons
        control_layout.addWidget(QLabel("Control Pad"))


        # Up Button
        up_button = QPushButton("Up")
        up_button.clicked.connect(self.move_up)
        control_layout.addWidget(up_button)

        # Left and Right Buttons
        left_right_layout = QHBoxLayout()
        left_button = QPushButton("Left")
        left_button.clicked.connect(self.move_left)
        right_button = QPushButton("Right")
        right_button.clicked.connect(self.move_right)
        left_right_layout.addWidget(left_button)
        left_right_layout.addWidget(right_button)
        control_layout.addLayout(left_right_layout)


        # Down Button
        down_button = QPushButton("Down")
        down_button.clicked.connect(self.move_down)
        control_layout.addWidget(down_button)



        move_CNC_button = QPushButton("Move to Position")
        move_CNC_button.clicked.connect(self.move_to_position)
        control_layout.addWidget(move_CNC_button)

        # Laser Parameters Tab Layout
        laser_param_layout = QVBoxLayout(laser_param_tab)

        # Title
        laser_param_title = QLabel("Laser Parameters")
        laser_param_title.setStyleSheet("font-weight: bold; font-size: 16px;")
        laser_param_title.setAlignment(Qt.AlignCenter)
        laser_param_layout.addWidget(laser_param_title)

        # Intensity
        intensity_layout = QHBoxLayout()
        intensity_label = QLabel("Intensity (mW/mm²):")
        self.intensity_input = QDoubleSpinBox()
        self.intensity_input.setRange(0.1, 10.0)
        self.intensity_input.setSingleStep(0.1)
        self.intensity_input.setValue(1.2)
        intensity_layout.addWidget(intensity_label)
        intensity_layout.addWidget(self.intensity_input)
        laser_param_layout.addLayout(intensity_layout)

        # Pulse Duration
        duration_layout = QHBoxLayout()
        duration_label = QLabel("Pulse Duration (ms):")
        self.duration_input = QDoubleSpinBox()
        self.duration_input.setRange(1, 1000)
        self.duration_input.setSingleStep(10)
        self.duration_input.setValue(100)
        duration_layout.addWidget(duration_label)
        duration_layout.addWidget(self.duration_input)
        laser_param_layout.addLayout(duration_layout)

        # Frequency
        frequency_layout = QHBoxLayout()
        frequency_label = QLabel("Frequency (Hz):")
        self.frequency_input = QDoubleSpinBox()
        self.frequency_input.setRange(0.1, 100.0)
        self.frequency_input.setSingleStep(0.1)
        self.frequency_input.setValue(0.5)
        frequency_layout.addWidget(frequency_label)
        frequency_layout.addWidget(self.frequency_input)
        laser_param_layout.addLayout(frequency_layout)

        # Spot Size
        spot_size_layout = QHBoxLayout()
        spot_size_label = QLabel("Spot Size (mm):")
        self.spot_size_input = QDoubleSpinBox()
        self.spot_size_input.setRange(0.1, 10.0)
        self.spot_size_input.setSingleStep(0.1)
        self.spot_size_input.setValue(3.7)
        spot_size_layout.addWidget(spot_size_label)
        spot_size_layout.addWidget(self.spot_size_input)
        laser_param_layout.addLayout(spot_size_layout)

        # Plot Area for Laser Parameters
        # Create figures and axes for the plots
        self.fig_signal = plt.Figure(figsize=(5, 2))
        self.canvas_signal = FigureCanvas(self.fig_signal)
        self.ax_signal = self.fig_signal.add_subplot(111)

        self.fig_spot = plt.Figure(figsize=(3, 3))
        self.canvas_spot = FigureCanvas(self.fig_spot)
        self.ax_spot = self.fig_spot.add_subplot(111)

        laser_param_layout.addWidget(QLabel("Intensity-Time Signal"))
        laser_param_layout.addWidget(self.canvas_signal)
        laser_param_layout.addWidget(QLabel("Spot Intensity Visualization"))
        laser_param_layout.addWidget(self.canvas_spot)

        # "Send Settings" Button
        send_settings_button = QPushButton("Send Settings")
        send_settings_button.clicked.connect(self.send_settings)
        laser_param_layout.addWidget(send_settings_button)

        # Connect signals to update plots
        self.intensity_input.valueChanged.connect(self.update_laser_plots)
        self.duration_input.valueChanged.connect(self.update_laser_plots)
        self.frequency_input.valueChanged.connect(self.update_laser_plots)
        self.spot_size_input.valueChanged.connect(self.update_laser_plots)

        # Initialize spot_circle
        self.spot_circle = None

        # Initial plot for laser parameters
        self.update_laser_plots()

        # Add tabs to the tab widget
        tab_widget.addTab(control_tab, "Control")
        tab_widget.addTab(laser_param_tab, "Laser Parameters")

        # Add the tab widget to the main layout
        main_layout.addWidget(tab_widget)

        self.setLayout(main_layout)

        # Initialize laser position at the center of the first well
        self.laser_x, self.laser_y = self.well_centers_raw[0]
        self.laser_position, = self.ax.plot(
            [], [], "ro", markersize=8, label="Laser Position"
        )
        self.update_laser_position(self.laser_x, self.laser_y)

        # Initial plot setup
        self.plot_plate()

        # Update laser position

        self.laser_position, = self.ax.plot([], [], 'ro', markersize=13, label="Laser Position")
        self.update_laser_position(self.laser_x, self.laser_y)
        

        self.stimulation_points = []
        for i in range(len(self.well_centers_raw)):
            point, = self.ax.plot([], [], "go", markersize=8, label=f"Stimulation Point {i + 1}")
            self.stimulation_points.append(point)

        for i in range(len(self.custom_stimulation_points)):
            self.update_calibration_position(i)

        # Initialize animation timer
        self.animation_timer = QTimer()
        self.animation_timer.timeout.connect(self.update_spot_animation)
        self.animation_interval = 50  # milliseconds
        self.animation_timer.start(self.animation_interval)
        self.animation_time = 0

    def plot_plate(self):
        """Plot the plate layout with a white platform background and wells at specified coordinates."""
        self.ax.clear()

        # Set up plot dimensions
        self.ax.set_xlim(0, self.platform_size[1])
        self.ax.set_ylim(0, self.platform_size[0])
        self.ax.set_aspect("equal")

        # Draw the platform background
        platform_rect = plt.Rectangle(
            (0, 0),
            self.platform_size[1],
            self.platform_size[0],
            edgecolor="black",
            linewidth=2,
            facecolor="white",
        )
        self.ax.add_patch(platform_rect)

        # Draw each well
        for i, (x_raw, y_raw) in enumerate(self.well_centers_raw):
            # Transform for display
            display_x, display_y = self.coords.raw_to_disp(x_raw, y_raw)
            display_y = self.platform_size[0] - display_y   # invert Y once

            # Create a rectangle representing the well
            square = plt.Rectangle(
                (display_x - self.well_size / 2, display_y - self.well_size / 2),
                self.well_size,
                self.well_size,
                edgecolor="black",
                linewidth=2,
                facecolor="orange",
                label=f"Well {i + 1}",
            )
            self.ax.add_patch(square)

            circle = plt.Circle(
                (display_x, display_y),
                self.circle_radius,
                color="blue",
                fill=False,
                linestyle="--",
            )
            self.ax.add_patch(circle)

            # Plot the center point of each well
            self.ax.plot(display_x, display_y, "ko")
            self.ax.text(
                display_x,
                display_y,
                f"Well {i + 1}",
                ha="center",
                va="center",
                color="white",
            )

        # Update laser position for display
        display_x = self.laser_y
        display_x, display_y = self.coords.raw_to_disp(self.laser_x, self.laser_y)
        display_y = self.platform_size[0] - display_y
        self.laser_position.set_data([display_x], [display_y])

        # Adjust plot aesthetics
        self.ax.invert_yaxis()
        self.ax.grid(visible=True, which="both", color="gray", linestyle="--", linewidth=0.5)
        self.ax.axis("off")

        # Redraw the canvas
        self.canvas.draw()

    def update_laser_position(self, x, y):
        """Update the laser position to a specific coordinate."""
        self.laser_x, self.laser_y = x, y                    # unchanged API
        display_x, display_y = self.coords.raw_to_disp(x, y)
        display_y = self.platform_size[0] - display_y        # invert once
        self.laser_position.set_data([display_x], [display_y])
        self.canvas.draw()

    def update_calibration_position(self, well_index):
        """Update the custom stimulation point position for a specific well."""
        stim_x, stim_y = self.custom_stimulation_points[well_index]
        # Transform for display
        display_x, display_y = self.coords.raw_to_disp(stim_x, stim_y)
        display_y = self.platform_size[0] - display_y
        self.stimulation_points[well_index].set_data([display_x], [display_y])
        self.canvas.draw()

    def set_stimulation_point(self, well_index):
        """Set the custom stimulation point to the current laser position."""
        # Store the actual coordinates
        self.custom_stimulation_points[well_index] = tuple(self.laser_raw)
        self.well_calibration_entries[well_index].setText(f"{self.custom_stimulation_points[well_index]}")

        # Update the specific well's stimulation point
        self.update_calibration_position(well_index)


    def _nudge(self, dx=0.0, dy=0.0):
        self.laser_raw[0] += dx
        self.laser_raw[1] += dy
        self.update_laser_position(*self.laser_raw)   # one call

    def move_up(self):
        self._nudge(dx=+self.laser_step, dy=0.0)
    def move_down(self):
        self._nudge(dx=-self.laser_step, dy=0.0)
    def move_left(self):
        self._nudge(dx=0.0, dy=-self.laser_step)
    def move_right(self):
        self._nudge(dx=0.0, dy=+self.laser_step)

    # def move_up(self):
    #     self._nudge(dx=0.0, dy=-self.laser_step)

    # def move_down(self):
    #     self._nudge(dx=0.0, dy=+self.laser_step)

    # def move_left(self):
    #     self._nudge(dx=-self.laser_step, dy=0.0)

    # def move_right(self):
    #     self._nudge(dx=+self.laser_step, dy=0.0)


    def update_laser_plots(self):
        """Update the laser parameter plots based on the selected parameters."""
        intensity = self.intensity_input.value()
        duration = self.duration_input.value()
        frequency = self.frequency_input.value()
        spot_size = self.spot_size_input.value()

        # Avoid division by zero
        if frequency == 0:
            frequency = 0.1

        # Reset animation time
        self.animation_time = 0

        # Clear the axes before plotting new data
        self.ax_signal.cla()
        self.ax_spot.cla()

        # Plotting the Intensity-Time Signal

        # Generate signal based on frequency and duration
        time_end = 2000  # ms
        time = np.linspace(0, time_end, 1000)
        pulse_interval = 1000 / frequency  # ms per cycle
        signal = np.zeros_like(time)

        for i, t in enumerate(time):
            if (t % pulse_interval) < duration:
                signal[i] = intensity

        # Plot signal
        self.ax_signal.plot(time, signal, label="Light Intensity", color="blue")
        self.ax_signal.set_xlabel("Time (ms)")
        self.ax_signal.set_ylabel("Intensity (mW/mm²)")
        self.ax_signal.set_ylim(0, max(intensity + 1, 2))
        self.ax_signal.set_title("Intensity-Time Signal")
        self.ax_signal.legend()
        self.ax_signal.grid(True)
        self.canvas_signal.draw()

        # Plotting the Spot Intensity Visualization

        # Set the axis limits
        max_size = spot_size * 1.2  # Add padding
        self.ax_spot.set_xlim(-max_size, max_size)
        self.ax_spot.set_ylim(-max_size, max_size)

        # Create the spot_circle
        self.spot_circle = plt.Circle(
            (0, 0),
            radius=spot_size,
            facecolor="blue",
            alpha=1.0,  # Initial alpha will be updated in animation
            edgecolor="black",
            label=f"Spot Size ({spot_size:.1f} mm)",
        )
        self.ax_spot.add_patch(self.spot_circle)

        self.ax_spot.set_aspect("equal", adjustable="box")
        self.ax_spot.axis("off")  # Hide axes for a cleaner look
        self.ax_spot.set_title("Spot Intensity Visualization")
        self.ax_spot.legend()
        self.canvas_spot.draw()

    def update_spot_animation(self):
        """Update the spot's alpha value to reflect frequency and pulse duration."""
        # Update animation time
        self.animation_time += self.animation_interval / 1000.0  # Convert ms to seconds

        intensity = self.intensity_input.value()
        frequency = self.frequency_input.value()
        pulse_duration_ms = self.duration_input.value()

        # Avoid division by zero
        if frequency == 0:
            frequency = 0.1

        # Calculate period and pulse duration in seconds
        period = 1.0 / frequency  # Period in seconds
        pulse_duration_sec = pulse_duration_ms / 1000.0  # Convert ms to seconds

        # Time within the current period
        time_in_period = self.animation_time % period

        if time_in_period < pulse_duration_sec:
            current_intensity = intensity
        else:
            current_intensity = 0

        # Update the spot's alpha
        normalized_intensity = current_intensity / self.intensity_input.maximum()
        alpha = max(0.05, min(normalized_intensity, 1.0))

        # Update the spot_circle's alpha if it exists
        if self.spot_circle:
            self.spot_circle.set_alpha(alpha)
            # Redraw the canvas
            self.canvas_spot.draw()

    def send_settings(self):
        """Send the current laser settings to the laser control system."""
        # Retrieve current settings
        intensity = self.intensity_input.value()
        pulse_duration = self.duration_input.value()
        frequency = self.frequency_input.value()
        spot_size = self.spot_size_input.value()

        # Check if Arduino controller is available
        if self.main_controller and self.main_controller.arduino_controller:
            try:
                # Send recipe command to Arduino
                self.main_controller.arduino_controller.send_recipe_command(
                    intensity=intensity,
                    pulse_duration=pulse_duration,
                    frequency=frequency,
                    on_time=pulse_duration  # Using pulse_duration as on_time
                )
                message = f"Laser settings sent successfully:\nIntensity: {intensity} mW/mm²\nPulse Duration: {pulse_duration} ms\nFrequency: {frequency} Hz\nSpot Size: {spot_size} mm"
                self.signal_emitter.log_message_signal.emit(message)
            except Exception as e:
                message = f"Error sending laser settings: {e}"
                self.signal_emitter.log_message_signal.emit(message)
        else:
            message = "Arduino controller not available. Please set the Arduino port."
            self.signal_emitter.log_message_signal.emit(message)


    def move_to_position(self):
        """Send the laser position settings to the machine system"""
        x = self.laser_x
        y = self.laser_y

        # Adjust coordinates if necessary (see next section)
        x_cnc, y_cnc = self.coords.raw_to_cnc(x, y)

        if self.main_controller and self.main_controller.printer_controller:
            try:
                self.main_controller.printer_controller.move_to(x_cnc, y_cnc)
                message = f"Moving CNC to position: X={x_cnc}, Y={y_cnc}"
                self.signal_emitter.log_message_signal.emit(message)
            except Exception as e:
                message = f"Error moving to position: {e}"
                self.signal_emitter.log_message_signal.emit(message)
        else:
            message = "Printer controller not available. Please set the G-code port."
            self.signal_emitter.log_message_signal.emit(message)
