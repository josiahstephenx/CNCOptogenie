# ui/components/MainWindow.py

from PySide6.QtWidgets import QMainWindow, QPushButton, QWidget, QStatusBar

class MainWindowUI(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("CNC Optogenie Controller")
        self.setGeometry(100, 100, 600, 400)
        
        # Main widget
        self.central_widget = QWidget(self)
        self.setCentralWidget(self.central_widget)

        # Run Recipe Button
        self.run_recipe_button = QPushButton("Run Recipe", self.central_widget)
        self.run_recipe_button.setGeometry(50, 50, 100, 40)
        
        # Emergency Stop Button
        self.emergency_stop_button = QPushButton("Emergency Stop", self.central_widget)
        self.emergency_stop_button.setGeometry(200, 50, 100, 40)
        
        # Status Bar
        self.status_bar = QStatusBar(self)
        self.setStatusBar(self.status_bar)



