# ui/components/TopBar.py

import serial.tools.list_ports
from PySide6.QtWidgets import QWidget, QPushButton, QHBoxLayout, QLabel, QComboBox

class TopBar(QWidget):
    def __init__(self, main_controller):
        super().__init__()
        self.main_controller = main_controller

        self.layout = QHBoxLayout()
        
        # Title Label
        self.title = QLabel("CNC Optogenie Controller")
        self.title.setStyleSheet("""
            font-size: 20px;
            font-weight: bold;
            color: #2c3e50;
            padding: 10px;
            background-color: #f8f9fa;
            border-radius: 8px;
        """)
        
        # Connected Button
        self.connected_button = QPushButton("Connected")
        self.connected_button.setStyleSheet("background-color: white; color: black;")
        
        # Emergency Stop Button
        self.emergency_stop_button = QPushButton("Emergency Stop")
        self.emergency_stop_button.setStyleSheet("background-color: red; color: white;")
        self.emergency_stop_button.clicked.connect(self.main_controller.emergency_stop)

        # Test Arduino Button
        self.test_arduino_button = QPushButton("Test Arduino")
        self.test_arduino_button.clicked.connect(self.main_controller.test_arduino_connection)

        # Test CNC Button
        self.test_cnc_button = QPushButton("Test CNC")
        self.test_cnc_button.clicked.connect(self.main_controller.test_cnc_connection)
        
        # Port selection for G-code printer
        self.gcode_port_combo = QComboBox()
        self.gcode_port_combo.setFixedWidth(120)
        self.gcode_port_combo.currentIndexChanged.connect(self.update_gcode_port)
        
        # Port selection for Arduino
        self.arduino_port_combo = QComboBox()
        self.arduino_port_combo.setFixedWidth(120)
        self.arduino_port_combo.currentIndexChanged.connect(self.update_arduino_port)
        
        # Populate available ports
        self.populate_ports()

        # Add widgets to layout
        self.layout.addWidget(self.title)
        self.layout.addStretch(1)
        self.layout.addWidget(QLabel("G-code Port:"))
        self.layout.addWidget(self.gcode_port_combo)
        self.layout.addWidget(QLabel("Arduino Port:"))
        self.layout.addWidget(self.arduino_port_combo)
        self.layout.addWidget(self.connected_button)
        self.layout.addWidget(self.emergency_stop_button)
        self.layout.addWidget(self.test_arduino_button)  # Add Test Arduino button
        self.layout.addWidget(self.test_cnc_button)  # Add Test CNC button

        self.setLayout(self.layout)

    def populate_ports(self):
        ports = serial.tools.list_ports.comports()
        self.gcode_port_combo.clear()
        self.arduino_port_combo.clear()
        for port in ports:
            self.gcode_port_combo.addItem(port.device)
            self.arduino_port_combo.addItem(port.device)

    def update_gcode_port(self):
        selected_port = self.gcode_port_combo.currentText()
        self.main_controller.set_gcode_port(selected_port)

    def update_arduino_port(self):
        selected_port = self.arduino_port_combo.currentText()
        self.main_controller.set_arduino_port(selected_port)
