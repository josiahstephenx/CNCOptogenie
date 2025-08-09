CNC_Optogenie_Controller/
│
├── CNCOptogenieController.py         # Main entry point for the application
├── requirements.txt                  # List of Python dependencies
├── README.md                         # Project documentation
├── config.yaml                       # Config file for application settings (optional)
│
├── assets/                           # Static assets (images, icons, etc.)
│   ├── icons/
│   ├── images/
│   └── styles.qss                    # Qt stylesheet file for custom styling
│
├── ui/                               # UI-related files
│   ├── MainWindow.ui                 # Main window UI file created with Qt Designer
│   ├── RecipeEditor.ui               # UI for recipe editor
│   ├── components/                   # Custom UI components
│   └── generated/                    # PySide6 generated Python files for .ui
│       ├── MainWindow_ui.py          # PySide6 generated Python code for MainWindow.ui
│       └── RecipeEditor_ui.py        # PySide6 generated Python code for RecipeEditor.ui
│
├── src/                              # Core application logic
│   ├── __init__.py
│   ├── main_controller.py            # Main application controller, handles UI interactions
│   ├── device_controller.py          # Controller for device communication via PySerial
│   ├── data_controller.py            # Controller for managing data (e.g., CRUD operations for SQLite)
│   ├── plot_controller.py            # Controller for managing Matplotlib or PyQtGraph visualizations
│   ├── models/                       # Data models
│   │   ├── recipe.py                 # Recipe data model
│   │   └── settings.py               # Settings data model
│   └── services/                     # Service layer for business logic
│       ├── recipe_service.py         # Recipe logic (e.g., validation, pattern creation)
│       └── device_service.py         # Device communication logic (e.g., sending recipes to device)
│
├── db/                               # Database and data-related files
│   ├── cnc_optogenie.db              # SQLite database file
│   ├── migrations/                   # Database migration scripts (if needed)
│   └── schema.sql                    # SQL schema for initializing the database
│
├── tests/                            # Test suite
│   ├── test_main_controller.py       # Unit tests for main_controller
│   ├── test_device_controller.py     # Unit tests for device_controller
│   ├── test_data_controller.py       # Unit tests for data_controller
│   └── fixtures/                     # Sample data for testing
│       └── sample_recipes.json       # Sample JSON data for testing recipes
│
└── packaging/                        # Packaging files for creating executables/installers
    ├── pyinstaller.spec              # PyInstaller spec file for packaging
    └── icons/                        # Icons for executables
