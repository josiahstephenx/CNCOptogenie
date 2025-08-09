# ui/styles.py

modern_style = """
    /* General Background */
    QWidget {
        background-color: #2e2e2e;
        color: #e0e0e0;
        font-family: Arial, sans-serif;
        font-size: 14px;
    }

    /* Title Styling */
    QLabel#Title {
        color: #ffffff;
        font-size: 20px;
        font-weight: bold;
    }

    /* Buttons */
    QPushButton {
        background-color: #5b5b5b;
        color: #ffffff;
        border-radius: 8px;
        padding: 8px 16px;
        border: none;
    }

    QPushButton:hover {
        background-color: #4a4a4a;
    }

    QPushButton:pressed {
        background-color: #6b6b6b;
    }

    /* Emergency Stop Button */
    QPushButton#EmergencyStop {
        background-color: #e53935;
        color: #ffffff;
    }

    QPushButton#EmergencyStop:hover {
        background-color: #d32f2f;
    }

    /* Connected Button */
    QPushButton#Connected {
        background-color: #66bb6a;
        color: #ffffff;
    }

    /* Combo Boxes */
    QComboBox {
        background-color: #424242;
        border: 1px solid #5b5b5b;
        padding: 5px;
        border-radius: 5px;
        color: #ffffff;
    }

    QComboBox QAbstractItemView {
        background-color: #424242;
        selection-background-color: #5b5b5b;
        color: #ffffff;
    }

    /* Status Bar */
    QStatusBar {
        background-color: #2e2e2e;
        color: #e0e0e0;
    }

    /* List Views */
    QListWidget {
        background-color: #3c3c3c;
        border: 1px solid #5b5b5b;
        color: #e0e0e0;
        padding: 5px;
    }
"""
