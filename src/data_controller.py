# src/data_controller.py

import sqlite3

class DataController:
    def __init__(self, db_path="db/cnc_optogenie.db"):
        self.db_path = db_path
        self.connection = None
        self.connect()

    def connect(self):
        self.connection = sqlite3.connect(self.db_path)
        self.connection.execute("PRAGMA foreign_keys = ON;")

    def initialize_db(self):
        with open("db/schema.sql", "r") as schema_file:
            schema = schema_file.read()
            self.connection.executescript(schema)
        self.connection.commit()

    # Recipe Methods
    def add_recipe(self, name, intensity, pulse_duration, frequency, spot_size):
        cursor = self.connection.cursor()
        cursor.execute(
            """
            INSERT INTO recipes (name, intensity, pulse_duration, frequency, spot_size)
            VALUES (?, ?, ?, ?, ?)
            """,
            (name, intensity, pulse_duration, frequency, spot_size)
        )
        self.connection.commit()
        return cursor.lastrowid

    def get_recipes(self):
        cursor = self.connection.cursor()
        cursor.execute("SELECT * FROM recipes ORDER BY name")
        return cursor.fetchall()

    def delete_recipe(self, recipe_id):
        cursor = self.connection.cursor()
        # First check if the recipe is used in any works
        cursor.execute("SELECT COUNT(*) FROM works WHERE recipe_id = ?", (recipe_id,))
        if cursor.fetchone()[0] > 0:
            raise Exception("Cannot delete recipe: it is used in one or more works")
        cursor.execute("DELETE FROM recipes WHERE id = ?", (recipe_id,))
        self.connection.commit()

    def get_recipe_by_id(self, recipe_id):
        """Get a recipe by its ID."""
        try:
            print(f"Fetching recipe with ID: {recipe_id}")
            cursor = self.connection.cursor()
            cursor.execute("""
                SELECT id, name, intensity, pulse_duration, frequency, spot_size 
                FROM recipes 
                WHERE id = ?
            """, (recipe_id,))
            recipe = cursor.fetchone()
            print(f"Found recipe: {recipe}")
            if recipe:
                return recipe
            print(f"No recipe found with ID: {recipe_id}")
            return None
        except Exception as e:
            print(f"Error fetching recipe: {str(e)}")
            return None

    # Work Methods
    def add_work(self, name, recipe_id, duration, status):
        cursor = self.connection.cursor()
        # Verify recipe exists
        if not self.get_recipe_by_id(recipe_id):
            raise Exception("Recipe not found")
        cursor.execute(
            """
            INSERT INTO works (name, recipe_id, duration, status)
            VALUES (?, ?, ?, ?)
            """,
            (name, recipe_id, duration, status)
        )
        self.connection.commit()
        return cursor.lastrowid

    def get_work_by_id(self, work_id):
        """Get a work by its ID."""
        cursor = self.connection.cursor()
        cursor.execute("""
            SELECT w.*, r.name as recipe_name 
            FROM works w 
            LEFT JOIN recipes r ON w.recipe_id = r.id 
            WHERE w.id = ?
        """, (work_id,))
        return cursor.fetchone()

    def get_works(self, status=None):
        cursor = self.connection.cursor()
        if status:
            cursor.execute("""
                SELECT w.*, r.name as recipe_name 
                FROM works w 
                LEFT JOIN recipes r ON w.recipe_id = r.id 
                WHERE w.status = ?
                ORDER BY w.id DESC
            """, (status,))
        else:
            cursor.execute("""
                SELECT w.*, r.name as recipe_name 
                FROM works w 
                LEFT JOIN recipes r ON w.recipe_id = r.id 
                ORDER BY w.id DESC
            """)
        return cursor.fetchall()

    def get_scheduled_works(self):
        """Fetch works with a 'Scheduled' status."""
        return self.get_works(status='Scheduled')

    def delete_work(self, work_id):
        cursor = self.connection.cursor()
        cursor.execute("DELETE FROM works WHERE id = ?", (work_id,))
        self.connection.commit()

    def update_work_status(self, work_id, new_status):
        cursor = self.connection.cursor()
        cursor.execute("UPDATE works SET status = ? WHERE id = ?", (new_status, work_id))
        self.connection.commit()

    def close(self):
        if self.connection:
            self.connection.close()
