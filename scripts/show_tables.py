import os
import sys
from pathlib import Path

# Add project root to Python path
project_root = str(Path(__file__).parent.parent)
sys.path.append(project_root)

from sqlalchemy import inspect, create_engine, text
from sqlalchemy.orm import sessionmaker
from config import DATABASE_URL

def show_tables():
    # Create engine and session
    engine = create_engine(DATABASE_URL)
    Session = sessionmaker(bind=engine)
    session = Session()
    
    # Get inspector
    inspector = inspect(engine)
    
    print("\n=== Database Tables ===")
    # Get all table names
    tables = inspector.get_table_names()
    print(f"Found {len(tables)} tables: {tables}\n")
    
    # For each table, show structure and data
    for table_name in tables:
        print(f"\n=== Table: {table_name} ===")
        
        # Show columns
        print("\nColumns:")
        columns = inspector.get_columns(table_name)
        for column in columns:
            print(f"- {column['name']}: {column['type']}")
        
        # Show data
        print("\nData:")
        try:
            # Use text() to properly wrap the SQL query
            result = session.execute(text(f"SELECT * FROM {table_name}"))
            rows = result.fetchall()
            if rows:
                for row in rows:
                    print(row)
            else:
                print("No data found")
        except Exception as e:
            print(f"Error fetching data: {e}")
        
        print("\n" + "="*50)

if __name__ == "__main__":
    show_tables()