import psycopg2
import os
from dotenv import load_dotenv

load_dotenv()

conn = psycopg2.connect(
    host=os.getenv("SUPABASE_HOST"),
    port=os.getenv("SUPABASE_PORT"),
    dbname=os.getenv("SUPABASE_DB"),
    user=os.getenv("SUPABASE_USER"),
    password=os.getenv("SUPABASE_PASSWORD")
)

cursor = conn.cursor()

cursor.execute("""
    CREATE TABLE IF NOT EXISTS userops (
        userOpHash TEXT PRIMARY KEY,
        transactionHash TEXT,
        sender TEXT,
        bundler TEXT,
        paymaster TEXT,
        blockNumber INTEGER,
        blockTimestamp INTEGER,
        network TEXT,
        collectedAt TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
""")

conn.commit()
conn.close()
print("Supabase table created successfully")