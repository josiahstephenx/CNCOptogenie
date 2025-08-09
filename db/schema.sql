-- db/schema.sql

CREATE TABLE IF NOT EXISTS recipes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    intensity REAL NOT NULL,
    pulse_duration INTEGER NOT NULL,
    frequency REAL NOT NULL,
    spot_size REAL NOT NULL
);

CREATE TABLE IF NOT EXISTS works (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    recipe_id INTEGER,
    duration INTEGER,
    status TEXT CHECK(status IN ('Scheduled', 'In Progress', 'Finished')) NOT NULL,
    FOREIGN KEY (recipe_id) REFERENCES recipes (id)
);
