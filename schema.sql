CREATE TABLE users (    user_id INTEGER PRIMARY KEY,    username TEXT NOT NULL,    password TEXT NOT NULL);

CREATE TABLE "habit" (    id INTEGER PRIMARY KEY AUTOINCREMENT,    user_id INTEGER NOT NULL,    habit TEXT NOT NULL,    number_of_habit INTEGER, created_at TIMESTAMP,    FOREIGN KEY (user_id) REFERENCES users(user_id));

CREATE TABLE habit_completion (    id INTEGER PRIMARY KEY AUTOINCREMENT,    user_id INTEGER NOT NULL,    habit_id INTEGER NOT NULL,    date DATE NOT NULL,    completed BOOLEAN DEFAULT 0,    FOREIGN KEY (user_id) REFERENCES users(user_id),    FOREIGN KEY (habit_id) REFERENCES habit(id),    UNIQUE(user_id, habit_id, date));

