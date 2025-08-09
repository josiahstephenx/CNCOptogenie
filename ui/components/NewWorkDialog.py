# ui/components/NewWorkDialog.py

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit,
    QComboBox, QSpinBox, QPushButton, QMessageBox
)
from src.data_controller import DataController

class NewWorkDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.data_controller = DataController()
        self.setWindowTitle("New Work")
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout()

        # Work Name
        name_layout = QHBoxLayout()
        name_label = QLabel("Name:")
        self.name_input = QLineEdit()
        name_layout.addWidget(name_label)
        name_layout.addWidget(self.name_input)

        # Recipe Selection
        recipe_layout = QHBoxLayout()
        recipe_label = QLabel("Recipe:")
        self.recipe_combo = QComboBox()
        self.load_recipes()
        recipe_layout.addWidget(recipe_label)
        recipe_layout.addWidget(self.recipe_combo)

        # Duration
        duration_layout = QHBoxLayout()
        duration_label = QLabel("Duration (seconds):")
        self.duration_input = QSpinBox()
        self.duration_input.setRange(1, 3600)  # 1 second to 1 hour
        self.duration_input.setValue(60)  # Default 1 minute
        duration_layout.addWidget(duration_label)
        duration_layout.addWidget(self.duration_input)

        # Buttons
        button_layout = QHBoxLayout()
        save_button = QPushButton("Save")
        cancel_button = QPushButton("Cancel")
        save_button.clicked.connect(self.save_work)
        cancel_button.clicked.connect(self.reject)
        button_layout.addWidget(save_button)
        button_layout.addWidget(cancel_button)

        # Add all layouts to main layout
        layout.addLayout(name_layout)
        layout.addLayout(recipe_layout)
        layout.addLayout(duration_layout)
        layout.addLayout(button_layout)

        self.setLayout(layout)

    def load_recipes(self):
        """Load recipes into the combo box."""
        recipes = self.data_controller.get_recipes()
        for recipe in recipes:
            self.recipe_combo.addItem(recipe[1], recipe[0])  # Display name, store ID

    def save_work(self):
        """Save the new work to the database."""
        name = self.name_input.text().strip()
        if not name:
            QMessageBox.warning(self, "Error", "Please enter a name for the work.")
            return

        recipe_id = self.recipe_combo.currentData()
        duration = self.duration_input.value()

        try:
            self.data_controller.add_work(name, recipe_id, duration, status="Scheduled")
            self.accept()
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Failed to save work: {str(e)}")
