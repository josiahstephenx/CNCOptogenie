from PySide6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QDoubleSpinBox,
    QSpinBox,
    QMessageBox
)
from PySide6.QtCore import QTimer
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
import matplotlib.pyplot as plt
import numpy as np
from src.data_controller import DataController


class NewRecipeDialog(QDialog):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("New Recipe")
        self.setFixedSize(600, 800)  # Adjusted size to accommodate plots

        self.data_controller = DataController()
        self.setup_ui()

        # Initialize spot_circle
        self.spot_circle = None

        # Initialize animation variables
        self.animation_timer = QTimer()
        self.animation_timer.timeout.connect(self.update_spot_animation)
        self.animation_interval = 50  # milliseconds
        self.animation_timer.start(self.animation_interval)
        self.animation_time = 0

        # Initial plot
        self.update_plot()

    def setup_ui(self):
        layout = QVBoxLayout()

        # Recipe Name
        name_layout = QHBoxLayout()
        name_label = QLabel("Recipe Name:")
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("Insert Name")
        name_layout.addWidget(name_label)
        name_layout.addWidget(self.name_input)

        # Settings layout
        settings_layout = QVBoxLayout()
        settings_label = QLabel("Settings")
        settings_label.setStyleSheet("font-weight: bold; font-size: 16px;")

        # Intensity
        intensity_layout = QHBoxLayout()
        intensity_label = QLabel("Intensity (%):")
        self.intensity_input = QDoubleSpinBox()
        self.intensity_input.setRange(0, 100)
        self.intensity_input.setValue(50)
        self.intensity_input.setDecimals(1)
        intensity_layout.addWidget(intensity_label)
        intensity_layout.addWidget(self.intensity_input)

        # Pulse Duration
        pulse_duration_layout = QHBoxLayout()
        pulse_duration_label = QLabel("Pulse Duration (ms):")
        self.pulse_duration_input = QSpinBox()
        self.pulse_duration_input.setRange(1, 1000)
        self.pulse_duration_input.setValue(100)
        pulse_duration_layout.addWidget(pulse_duration_label)
        pulse_duration_layout.addWidget(self.pulse_duration_input)

        # Frequency
        frequency_layout = QHBoxLayout()
        frequency_label = QLabel("Frequency (Hz):")
        self.frequency_input = QDoubleSpinBox()
        self.frequency_input.setRange(0.1, 100)
        self.frequency_input.setValue(1)
        self.frequency_input.setDecimals(1)
        frequency_layout.addWidget(frequency_label)
        frequency_layout.addWidget(self.frequency_input)

        # Spot Size
        spot_size_layout = QHBoxLayout()
        spot_size_label = QLabel("Spot Size (mm):")
        self.spot_size_input = QDoubleSpinBox()
        self.spot_size_input.setRange(0.1, 10)
        self.spot_size_input.setValue(1)
        self.spot_size_input.setDecimals(1)
        spot_size_layout.addWidget(spot_size_label)
        spot_size_layout.addWidget(self.spot_size_input)

        # Add settings to layout
        settings_layout.addWidget(settings_label)
        settings_layout.addLayout(intensity_layout)
        settings_layout.addLayout(pulse_duration_layout)
        settings_layout.addLayout(frequency_layout)
        settings_layout.addLayout(spot_size_layout)

        # Plot Area
        # Create figures and axes once
        self.fig_signal = plt.Figure(figsize=(5, 2))
        self.canvas_signal = FigureCanvas(self.fig_signal)
        self.ax_signal = self.fig_signal.add_subplot(111)

        self.fig_spot = plt.Figure(figsize=(3, 3))
        self.canvas_spot = FigureCanvas(self.fig_spot)
        self.ax_spot = self.fig_spot.add_subplot(111)

        layout.addLayout(name_layout)
        layout.addLayout(settings_layout)
        layout.addWidget(QLabel("Intensity-Time Signal"))
        layout.addWidget(self.canvas_signal)
        layout.addWidget(QLabel("Spot Intensity Visualization"))
        layout.addWidget(self.canvas_spot)

        # Create Recipe Button
        button_layout = QHBoxLayout()
        save_button = QPushButton("Save")
        cancel_button = QPushButton("Cancel")
        save_button.clicked.connect(self.save_recipe)
        cancel_button.clicked.connect(self.reject)
        button_layout.addWidget(save_button)
        button_layout.addWidget(cancel_button)

        layout.addLayout(button_layout)
        self.setLayout(layout)

        # Update plot on parameter changes
        self.intensity_input.valueChanged.connect(self.update_plot)
        self.pulse_duration_input.valueChanged.connect(self.update_plot)
        self.frequency_input.valueChanged.connect(self.update_plot)
        self.spot_size_input.valueChanged.connect(self.update_plot)

    def update_plot(self):
        """Update both plots based on the selected parameters."""
        intensity = self.intensity_input.value()
        pulse_duration = self.pulse_duration_input.value()
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
            if (t % pulse_interval) < pulse_duration:
                signal[i] = intensity

        # Plot signal
        self.ax_signal.plot(time, signal, label="Light Intensity", color='blue')
        self.ax_signal.set_xlabel("Time (ms)")
        self.ax_signal.set_ylabel("Intensity (mW/mm²)")
        self.ax_signal.set_ylim(0, max(intensity + 1, 2))
        self.ax_signal.set_title("Intensity-Time Signal")
        self.ax_signal.legend()
        self.ax_signal.grid(True)
        self.canvas_signal.draw()

        # Plotting the Spot Intensity Visualization

        # Set the axis limits based on spot_size
        max_size = spot_size * 1.2  # Add padding
        self.ax_spot.set_xlim(-max_size, max_size)
        self.ax_spot.set_ylim(-max_size, max_size)

        # Create the spot_circle
        self.spot_circle = plt.Circle(
            (0, 0),
            radius=spot_size,
            facecolor='blue',
            alpha=1.0,  # Initial alpha will be updated in animation
            edgecolor='black',
            label=f'Spot Size ({spot_size:.1f} mm)'
        )
        self.ax_spot.add_patch(self.spot_circle)

        self.ax_spot.set_aspect('equal', adjustable='box')
        self.ax_spot.axis('off')  # Hide axes for a cleaner look
        self.ax_spot.set_title("Spot Intensity Visualization")
        self.ax_spot.legend()
        self.canvas_spot.draw()

    def update_spot_animation(self):
        """Update the spot's alpha value to reflect frequency and pulse duration."""
        # Update animation time
        self.animation_time += self.animation_interval / 1000.0  # Convert ms to seconds

        intensity = self.intensity_input.value()
        frequency = self.frequency_input.value()
        pulse_duration_ms = self.pulse_duration_input.value()

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
        alpha = max(0.1, min(normalized_intensity, 1.0))

        # Update the spot_circle's alpha if it exists
        if self.spot_circle:
            self.spot_circle.set_alpha(alpha)
            # Redraw the canvas
            self.canvas_spot.draw()

    def save_recipe(self):
        """Save the new recipe to the database."""
        name = self.name_input.text().strip()
        if not name:
            QMessageBox.warning(self, "Error", "Please enter a name for the recipe.")
            return

        intensity = self.intensity_input.value()
        pulse_duration = self.pulse_duration_input.value()
        frequency = self.frequency_input.value()
        spot_size = self.spot_size_input.value()

        try:
            self.data_controller.add_recipe(name, intensity, pulse_duration, frequency, spot_size)
            self.accept()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to save recipe: {str(e)}")
