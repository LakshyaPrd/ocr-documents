"""
Simple script to add raw_ocr_text column to documents table
"""
import sqlite3

# Connect to database
conn = sqlite3.connect('ocr_data.db')
cursor = conn.cursor()

try:
    # Add raw_ocr_text column
    cursor.execute("ALTER TABLE documents ADD COLUMN raw_ocr_text TEXT")
    conn.commit()
    print("✅ Added raw_ocr_text column successfully")
except Exception as e:
    print(f"Column might already exist or error: {e}")

conn.close()
