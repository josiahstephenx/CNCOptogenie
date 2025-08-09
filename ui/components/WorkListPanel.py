# ui/components/WorkListPanel.py

from PySide6.QtWidgets import (
    QWidget, QLabel, QVBoxLayout, QPushButton, QListWidget, 
    QListWidgetItem, QMessageBox, QHBoxLayout, QMenu, QFrame, QMainWindow, QDialog, QProgressBar
)
from PySide6.QtCore import Qt, QObject, Signal, QTimer, QThread
from src.data_controller import DataController
from ui.components.NewWorkDialog import NewWorkDialog
from src.main_controller import MainController
import time

class SignalEmitter(QObject):
    log_message_signal = Signal(str)

class ArduinoWorker(QThread):
    finished = Signal(bool, str)  # Signal with success status and message
    
    def __init__(self, arduino_controller, recipe, duration):
        super().__init__()
        self.arduino_controller = arduino_controller
        self.duration = duration
        self.recipe = recipe
        self._is_running = True
        
    def stop(self):
        self._is_running = False
        
    def run(self):
        try:
            # Debug print recipe values
            print(f"Recipe values:")
            print(f"  ID: {self.recipe[0]}")
            print(f"  Name: {self.recipe[1]}")
            print(f"  Intensity: {self.recipe[2]}")
            print(f"  Pulse Duration: {self.recipe[3]}")
            print(f"  Frequency: {self.recipe[4]}")
            print(f"  Spot Size: {self.recipe[5]}")
            
            # Send recipe command to Arduino
            self.arduino_controller.send_recipe_command(
                self.recipe[2],      # intensity
                self.duration,      # pulse_duration
                self.recipe[4],      # frequency
                self.recipe[3]       # on_time (default 1ms)
            )
            
            # Wait for recipe completion
            while self._is_running:
                response = self.arduino_controller.await_response("DONE", timeout=1)  # Check every second
                if response:
                    self.finished.emit(True, "Recipe completed successfully")
                    return
                # If no response, continue waiting
                
            # If we get here, the thread was stopped
            self.finished.emit(False, "Recipe execution was cancelled")
            
        except Exception as e:
            self.finished.emit(False, str(e))


class WorkProgressWindow(QDialog):
    def __init__(self, parent=None, duration=0):
        super().__init__(parent)
        self.setWindowTitle("Work Progress")
        self.setFixedSize(400, 200)
        self.setWindowFlags(Qt.Window | Qt.WindowStaysOnTopHint)  # Make it stay on top
        self.duration = duration  # Store the duration in seconds
        self.remaining_time = duration  # Initialize remaining time
        self.setup_ui()
        
    def setup_ui(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        
        # Title
        title_label = QLabel("Work in Progress")
        title_label.setStyleSheet("""
            font-size: 18px;
            font-weight: bold;
            color: #2c3e50;
            padding: 10px;
        """)
        title_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(title_label)
        
        # Time label with larger font and border
        self.time_label = QLabel("00:00:00")
        self.time_label.setStyleSheet("""
            font-size: 36px;
            font-weight: bold;
            color: #2980b9;
            background-color: #ecf0f1;
            border: 2px solid #bdc3c7;
            border-radius: 10px;
            padding: 20px;
        """)
        self.time_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.time_label)
        
        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                border: 2px solid #bdc3c7;
                border-radius: 5px;
                text-align: center;
                height: 25px;
            }
            QProgressBar::chunk {
                background-color: #2980b9;
                border-radius: 3px;
            }
        """)
        self.progress_bar.setMaximum(100)
        self.progress_bar.setValue(0)
        layout.addWidget(self.progress_bar)
        
        # Status label
        self.status_label = QLabel("Remaining Time")
        self.status_label.setStyleSheet("""
            font-size: 14px;
            color: #7f8c8d;
        """)
        self.status_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.status_label)
        
        # Cancel button
        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.setStyleSheet("""
            QPushButton {
                background-color: #e74c3c;
                color: white;
                border: none;
                padding: 10px;
                border-radius: 5px;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #c0392b;
            }
        """)
        self.cancel_button.setFixedWidth(150)
        self.cancel_button.clicked.connect(self.cancel_work)
        layout.addWidget(self.cancel_button, alignment=Qt.AlignCenter)
        
        self.setLayout(layout)
        
        # Setup timer
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_time)
        self.timer.start(1000)  # Update every second
        
        # Show the window
        self.show()
        
    def update_time(self):
        if self.remaining_time > 0:
            self.remaining_time -= 1
            hours = self.remaining_time // 3600
            minutes = (self.remaining_time % 3600) // 60
            seconds = self.remaining_time % 60
            self.time_label.setText(f"{hours:02d}:{minutes:02d}:{seconds:02d}")
            
            # Update progress bar
            progress = int((self.duration - self.remaining_time) / self.duration * 100)
            self.progress_bar.setValue(progress)
        else:
            self.timer.stop()
            self.close()
        
    def cancel_work(self):
        if hasattr(self, 'parent') and hasattr(self.parent(), 'arduino_worker'):
            self.parent().arduino_worker.stop()
        self.close()
        
    def closeEvent(self, event):
        if hasattr(self, 'timer'):
            self.timer.stop()
        super().closeEvent(event)

class WorkItemWidget(QWidget):
    def __init__(self, work_id, work_data, parent=None):
        super().__init__(parent)
        self.work_id = work_id
        self.work_data = work_data
        self.work_list_panel = parent  # Store reference to the WorkListPanel
        self.progress_window = None  # Store reference to progress window
        self.arduino_worker = None  # Store reference to Arduino worker
        self.setup_ui()
        
    def setup_ui(self):
        layout = QHBoxLayout()
        layout.setContentsMargins(5, 2, 5, 2)
        
        # Work info
        info_layout = QVBoxLayout()
        info_layout.setSpacing(2)
        
        # Recipe name and status
        recipe_name = self.work_data[1]  # Recipe name is in the second column
        status = self.work_data[2]  # Status is in the third column
        status_label = QLabel(f"{recipe_name} - {status}")
        status_label.setStyleSheet("font-weight: bold;")
        info_layout.addWidget(status_label)
        
        # Work details
        details_label = QLabel(f"ID: {self.work_id}")
        info_layout.addWidget(details_label)
        
        layout.addLayout(info_layout)
        layout.addStretch()
        
        # Buttons
        button_layout = QHBoxLayout()
        button_layout.setSpacing(5)
        
        # Start button
        start_btn = QPushButton("Start")
        start_btn.setFixedWidth(80)
        start_btn.clicked.connect(self.start_work)
        button_layout.addWidget(start_btn)
        
        # Delete button
        delete_btn = QPushButton("Delete")
        delete_btn.setFixedWidth(80)
        delete_btn.setStyleSheet("background-color: #ff4444; color: white;")
        delete_btn.clicked.connect(self.delete_work)
        button_layout.addWidget(delete_btn)
        
        layout.addLayout(button_layout)
        self.setLayout(layout)
        
        # Set background color based on status
        if status == "Finished":
            self.setStyleSheet("background-color: #e8f5e9;")
        elif status == "In Progress":
            self.setStyleSheet("background-color: #fff3e0;")
        else:
            self.setStyleSheet("background-color: white;")
            
    def start_work(self):
        """Start the work execution."""
        try:
            # Get the main window from the parent
            main_window = self.window()
            if not main_window:
                raise Exception("Could not find main window")
            
            # Check if Arduino controller is available
            if not main_window.main_controller.arduino_controller:
                raise Exception("Arduino controller not available. Please set the Arduino port first.")
            
            # Get work details
            work = main_window.main_controller.data_controller.get_work_by_id(self.work_id)
            if not work:
                raise Exception(f"Work with ID {self.work_id} not found")
            
            # Debug print work data
            print(f"Work data:")
            print(f"  ID: {work[0]}")
            print(f"  Name: {work[1]}")
            print(f"  Recipe ID: {work[2]}")
            print(f"  Duration: {work[3]}")
            print(f"  Status: {work[4]}")
            
            # Get recipe ID from work data (it's in the second column)
            recipe_id = work[2]  # Index 2 contains the recipe_id
            
            # Get recipe details
            recipe = main_window.main_controller.data_controller.get_recipe_by_id(recipe_id)
            if not recipe:
                raise Exception(f"Recipe with ID {recipe_id} not found")
            
            # Debug print recipe data
            print(f"Recipe data:")
            print(f"  ID: {recipe[0]}")
            print(f"  Name: {recipe[1]}")
            print(f"  Intensity: {recipe[2]}")
            print(f"  Pulse Duration: {recipe[3]}")
            print(f"  Frequency: {recipe[4]}")
            print(f"  Spot Size: {recipe[5]}")
            
            # Update work status to "In Progress"
            main_window.main_controller.data_controller.update_work_status(self.work_id, "In Progress")
            
            # Show progress window with duration
            self.progress_window = WorkProgressWindow(self, work[3])

            pg = main_window.plate_grid
            coords = pg.coords
            success = True  # Track overall success

            for idx, (x_raw, y_raw) in enumerate(pg.custom_stimulation_points):
                # Clean up any existing worker
                if self.arduino_worker and self.arduino_worker.isRunning():
                    self.arduino_worker.stop()
                    self.arduino_worker.wait()  # Wait for the thread to finish
                    self.arduino_worker = None

                x_cnc, y_cnc = coords.raw_to_cnc(x_raw, y_raw) # swap only

                main_window.main_controller.log_message(f"Moving to stimulation point {idx}: CNC ({x_cnc:.2f}, {y_cnc:.2f})")
                                    
                # Move to position
                main_window.main_controller.printer_controller.move_to(x_cnc, y_cnc)
                main_window.main_controller.printer_controller.wait_for_move_completion()
                
                # Wait for stability
                main_window.main_controller.log_message("Waiting for stability...")
                time.sleep(5)  # Wait 5 seconds for stability
                
                # Create and start Arduino worker
                self.arduino_worker = ArduinoWorker(main_window.main_controller.arduino_controller, recipe, work[3])
                self.arduino_worker.start()

                # Wait for the worker to complete
                time.sleep(work[3]+2)  # Wait for the duration plus buffer

                # Check if worker completed successfully
                if not self.arduino_worker.isRunning():
                    success = False
                    break

            # Clean up the final worker
            if self.arduino_worker:
                self.arduino_worker.stop()
                self.arduino_worker.wait()
                self.arduino_worker = None

            # Emit single completion signal
            if success:
                self.handle_arduino_completion(True, "Sequence completed successfully")
            else:
                self.handle_arduino_completion(False, "Sequence was cancelled")
            
        except Exception as e:
            error_msg = f"Error executing work {self.work_id}: {str(e)}"
            print(error_msg)
            main_window.main_controller.log_message(error_msg)
            if self.progress_window:
                self.progress_window.close()
            self.progress_window = None

    def handle_arduino_completion(self, success, message):
        """Handle the completion of Arduino work."""
        main_window = self.window()
        
        if success:
            # Update work status to "Finished"
            main_window.main_controller.data_controller.update_work_status(self.work_id, "Finished")
            
            # Update UI
            self.work_data = main_window.main_controller.data_controller.get_work_by_id(self.work_id)
            self.setup_ui()
            
            # Log success
            main_window.main_controller.log_message(f"Work {self.work_id} completed successfully")
        else:
            # Update work status back to "Scheduled"
            main_window.main_controller.data_controller.update_work_status(self.work_id, "Scheduled")
            main_window.main_controller.log_message(f"Error executing work {self.work_id}: {message}")
        
        # Close progress window
        if self.progress_window:
            self.progress_window.close()
            self.progress_window = None

    def delete_work(self):
        """Delete the work after confirmation."""
        try:
            # Get the main window from the parent
            main_window = self.window()
            if not main_window:
                raise Exception("Could not find main window")
            
            # Confirm deletion
            reply = QMessageBox.question(
                self,
                'Confirm Deletion',
                f'Are you sure you want to delete work {self.work_id}?',
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )
            
            if reply == QMessageBox.Yes:
                # Delete the work
                main_window.main_controller.data_controller.delete_work(self.work_id)
                
                # Remove this widget from the parent
                if self.work_list_panel:
                    self.work_list_panel.remove_work_item(self)
                
                # Log success
                main_window.main_controller.log_message(f"Work {self.work_id} deleted successfully")
                
        except Exception as e:
            if main_window:
                main_window.main_controller.log_message(f"Error deleting work {self.work_id}: {str(e)}")
            raise

class WorkListPanel(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.main_window = parent
        self.data_controller = DataController()  # Keep a local reference to DataController
        self.setup_ui()
        
    def setup_ui(self):
        layout = QVBoxLayout()
        
        # Title
        title_label = QLabel("Scheduled Works")
        title_label.setStyleSheet("font-size: 16px; font-weight: bold; margin-bottom: 10px;")
        layout.addWidget(title_label)
        
        # Work list
        self.work_list_layout = QVBoxLayout()
        self.work_list_layout.setSpacing(5)
        layout.addLayout(self.work_list_layout)
        
        # Add work button
        add_work_btn = QPushButton("Add New Work")
        add_work_btn.clicked.connect(self.show_new_work_dialog)
        layout.addWidget(add_work_btn)
        
        self.setLayout(layout)
        self.refresh_work_list()
        
    def refresh_work_list(self):
        """Refresh the work list from the database."""
        # Clear existing items
        while self.work_list_layout.count():
            item = self.work_list_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        
        # Get works from database
        works = self.data_controller.get_works()
        
        # Add work items
        for work in works:
            work_id = work[0]
            work_name = work[1]
            recipe_name = work[2]
            duration = work[3]
            status = work[4]
            
            work_item = WorkItemWidget(
                work_id=work_id,
                work_data=(work_id, work_name, recipe_name, duration, status),
                parent=self
            )
            self.work_list_layout.addWidget(work_item)
    
    def show_new_work_dialog(self):
        """Open dialog to create new work."""
        dialog = NewWorkDialog(self)
        if dialog.exec() == QDialog.Accepted:
            self.refresh_work_list()
    
    def remove_work_item(self, work_item):
        """Remove a work item from the list."""
        self.work_list_layout.removeWidget(work_item)
        work_item.deleteLater()
        self.refresh_work_list()
