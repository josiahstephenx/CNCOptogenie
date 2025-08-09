# tests/test_data_controller.py

import pytest
from src.data_controller import DataController

@pytest.fixture
def db_controller():
    # Initialize in-memory database for testing
    controller = DataController(":memory:")
    controller.initialize_db()
    yield controller
    controller.close()

def test_add_and_get_recipe(db_controller):
    db_controller.add_recipe("Test Recipe", 1.5, 20, 10)
    recipes = db_controller.get_all_recipes()
    assert len(recipes) == 1
    assert recipes[0][1] == "Test Recipe"
