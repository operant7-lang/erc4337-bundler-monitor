import sqlite3

# Creates a database file called userops.db in your folder
conn = sqlite3.connect("userops.db")
cursor = conn.cursor()

# Creates a table to store UserOps
cursor.execute("""
    CREATE TABLE IF NOT EXISTS userops (
        userOpHash TEXT PRIMARY KEY,
        transactionHash TEXT,
        sender TEXT,
        bundler TEXT,
        paymaster TEXT,
        maxFeePerGas TEXT,
        maxPriorityFeePerGas TEXT,
        success INTEGER,
        nonce TEXT,
        network TEXT,
        collectedAt TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
""")

conn.commit()
conn.close()
print("Database created successfully")