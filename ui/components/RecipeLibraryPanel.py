# ui/components/RecipeLibraryPanel.py

from PySide6.QtWidgets import (
    QWidget, QLabel, QVBoxLayout, QPushButton, QListWidget, 
    QListWidgetItem, QMessageBox, QHBoxLayout, QMenu
)
from PySide6.QtCore import Qt
from ui.components.NewRecipeDialog import NewRecipeDialog
from src.data_controller import DataController

class RecipeLibraryPanel(QWidget):
    def __init__(self):
        super().__init__()
        self.setFixedWidth(200)
        self.data_controller = DataController()

        layout = QVBoxLayout()
        
        # Title
        title = QLabel("Recipe Library")
        title.setStyleSheet("font-weight: bold; font-size: 16px;")
        
        # Recipe List
        self.recipe_list = QListWidget()
        self.recipe_list.setContextMenuPolicy(Qt.CustomContextMenu)
        self.recipe_list.customContextMenuRequested.connect(self.show_context_menu)
        
        # Load recipes from the database
        self.load_recipes()

        # Buttons Layout
        button_layout = QHBoxLayout()
        
        # New and Delete Buttons
        new_button = QPushButton("New")
        delete_button = QPushButton("Delete")
        
        # Connect buttons
        new_button.clicked.connect(self.open_new_recipe_dialog)
        delete_button.clicked.connect(self.delete_selected_recipe)

        # Add buttons to layout
        button_layout.addWidget(new_button)
        button_layout.addWidget(delete_button)

        # Add widgets to main layout
        layout.addWidget(title)
        layout.addWidget(self.recipe_list)
        layout.addLayout(button_layout)
        
        self.setLayout(layout)

    def load_recipes(self):
        """Load recipes from the database and display them in the list."""
        recipes = self.data_controller.get_recipes()
        self.recipe_list.clear()
        for recipe in recipes:
            recipe_id = recipe[0]
            recipe_name = recipe[1]
            item = QListWidgetItem(recipe_name)
            item.setData(Qt.UserRole, recipe_id)  # Store recipe ID in the item
            self.recipe_list.addItem(item)

    def open_new_recipe_dialog(self):
        """Open the New Recipe Dialog."""
        dialog = NewRecipeDialog()
        if dialog.exec():
            self.load_recipes()

    def delete_selected_recipe(self):
        """Delete the selected recipe after confirmation."""
        current_item = self.recipe_list.currentItem()
        if not current_item:
            QMessageBox.warning(self, "No Selection", "Please select a recipe to delete.")
            return

        recipe_id = current_item.data(Qt.UserRole)
        recipe_name = current_item.text()

        reply = QMessageBox.question(
            self,
            "Confirm Deletion",
            f"Are you sure you want to delete the recipe '{recipe_name}'?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            try:
                self.data_controller.delete_recipe(recipe_id)
                self.load_recipes()
                QMessageBox.information(self, "Success", "Recipe deleted successfully.")
            except Exception as e:
                QMessageBox.critical(self, "Error", str(e))

    def show_context_menu(self, position):
        """Show context menu for recipe list."""
        menu = QMenu()
        delete_action = menu.addAction("Delete")
        
        action = menu.exec_(self.recipe_list.mapToGlobal(position))
        if action == delete_action:
            self.delete_selected_recipe()
