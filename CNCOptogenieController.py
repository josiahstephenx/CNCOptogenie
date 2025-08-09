# CNCOptogenieController.py

import sys
from PySide6.QtWidgets import QApplication, QMainWindow, QHBoxLayout, QVBoxLayout, QWidget, QPushButton, QTextEdit
from ui.components.TopBar import TopBar
from ui.components.WorkListPanel import WorkListPanel
from ui.components.RecipeLibraryPanel import RecipeLibraryPanel
from ui.components.PlateGrid import PlateGrid
from src.data_controller import DataController
from src.main_controller import MainController
from ui.styles import modern_style  # Import the style sheet

class CNCOptogenieController(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("CNC Optogenie Controller")
        self.setGeometry(100, 100, 900, 550)

        self.setStyleSheet("""
            QMainWindow {
                background-color: #f8f9fa;
            }
            QWidget {
                background-color: #f8f9fa;
                color: #2c3e50;
            }
        """)

        # Initialize the database
        self.data_controller = DataController()
        self.data_controller.initialize_db()

        # Initialize MainController without ports
        self.main_controller = MainController(self)

        # Main Layout
        main_widget = QWidget()
        main_layout = QVBoxLayout()
        main_widget.setLayout(main_layout)
        
        # Top Bar with port selection
        self.top_bar = TopBar(self.main_controller)
        main_layout.addWidget(self.top_bar)
        
        # Start Sequence Button
        self.start_sequence_button = QPushButton("Start Sequence")
        self.start_sequence_button.clicked.connect(self.start_sequence)
        self.start_sequence_button.setStyleSheet("background-color: #2962ff; color: white; border-radius: 8px;")
        main_layout.addWidget(self.start_sequence_button)

        # Log Window
        self.log_window = QTextEdit()
        self.log_window.setReadOnly(True)
        self.log_window.setStyleSheet("""
            QTextEdit {
                background-color: #1e1e1e;
                color: #d4d4d4;
                font-family: Monaco, monospace;
                font-size: 12px;
            }
        """)
        main_layout.addWidget(self.log_window)
        
        # Body Layout
        body_layout = QHBoxLayout()
        
        # Left Panel
        left_panel = QVBoxLayout()
        self.work_list_panel = WorkListPanel()
        self.recipe_library_panel = RecipeLibraryPanel()
        left_panel.addWidget(self.work_list_panel)
        left_panel.addWidget(self.recipe_library_panel)
        
        # Center Plate Area with CNC Movement Grid
        self.plate_grid = PlateGrid(main_controller=self.main_controller)
        self.plate_grid.signal_emitter.log_message_signal.connect(self.log_message)
        
        # Add to Body Layout
        body_layout.addLayout(left_panel)
        body_layout.addWidget(self.plate_grid)
        
        main_layout.addLayout(body_layout)
        
        self.setCentralWidget(main_widget)

    def log_message(self, message):
        """Append a log message to the log window."""
        if hasattr(self, 'log_window'):
            self.log_window.append(message)
        print(message)  # Also print to console for debugging

    def start_sequence(self):
        """Start the sequence for moving and activating the LED."""
        self.log_message("Starting sequence...")
        self.main_controller.execute_sequence()

    def closeEvent(self, event):
        """Override the close event to ensure all connections are closed."""
        self.main_controller.close_connections()
        self.log_message("Closed connections.")
        event.accept()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = CNCOptogenieController()
    window.show()
    sys.exit(app.exec())
