import sqlite3
from datetime import datetime

# Connect to SQLite database (creates it if it doesn't exist)
conn = sqlite3.connect('piglets.db')
cursor = conn.cursor()

# Create MalePiglets table
cursor.execute('''
CREATE TABLE IF NOT EXISTS MalePiglets (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    barcode TEXT UNIQUE NOT NULL,
    birth_date DATE,
    breed TEXT,
    weight REAL,
    health_status TEXT,
    mother_id INTEGER,
    father_id INTEGER,
    location TEXT,
    notes TEXT
)
''')

# Create FemalePiglets table
cursor.execute('''
CREATE TABLE IF NOT EXISTS FemalePiglets (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    barcode TEXT UNIQUE NOT NULL,
    birth_date DATE,
    breed TEXT,
    weight REAL,
    health_status TEXT,
    mother_id INTEGER,
    father_id INTEGER,
    location TEXT,
    notes TEXT
)
''')

conn.commit()

def add_piglet(gender, barcode, birth_date, breed, weight, health_status, mother_id, father_id, location, notes):
    table = 'MalePiglets' if gender.lower() == 'male' else 'FemalePiglets'
    try:
        cursor.execute(f'''
        INSERT INTO {table} (barcode, birth_date, breed, weight, health_status, mother_id, father_id, location, notes)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (barcode, birth_date, breed, weight, health_status, mother_id, father_id, location, notes))
        conn.commit()
        print(f"{gender.capitalize()} piglet with barcode {barcode} added successfully.")
    except sqlite3.IntegrityError:
        print(f"Error: Piglet with barcode {barcode} already exists.")

def scan_piglet():
    print("Scan piglet details:")
    gender = input("Gender (Male/Female): ").strip()
    barcode = input("Barcode: ").strip()
    birth_date = input("Birth Date (YYYY-MM-DD): ").strip()
    breed = input("Breed: ").strip()
    weight = float(input("Weight (kg): ").strip())
    health_status = input("Health Status: ").strip()
    mother_id = input("Mother ID (optional): ").strip() or None
    father_id = input("Father ID (optional): ").strip() or None
    location = input("Location: ").strip()
    notes = input("Notes: ").strip()
    
    # Convert mother/father IDs to integers if provided
    mother_id = int(mother_id) if mother_id else None
    father_id = int(father_id) if father_id else None

    add_piglet(gender, barcode, birth_date, breed, weight, health_status, mother_id, father_id, location, notes)

# Example usage
if __name__ == "__main__":
    while True:
        scan_piglet()
        cont = input("Scan another piglet? (y/n): ").strip().lower()
        if cont != 'y':
            break

conn.close()
