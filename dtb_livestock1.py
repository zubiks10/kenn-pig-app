import sqlite3
from tabulate import tabulate

# Connect to the database
conn = sqlite3.connect('piglets.db')
cursor = conn.cursor()

def view_table(table_name):
    cursor.execute(f"SELECT * FROM {table_name}")
    rows = cursor.fetchall()
    
    # Get column names
    col_names = [description[0] for description in cursor.description]
    
    print(f"\n📋 Contents of {table_name}:")
    if rows:
        print(tabulate(rows, headers=col_names, tablefmt="grid"))
    else:
        print("(No records found)")

# View both tables
view_table('MalePiglets')
view_table('FemalePiglets')

conn.close()
