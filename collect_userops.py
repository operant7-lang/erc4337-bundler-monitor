import requests
import psycopg2
import time
from dotenv import load_dotenv
import os

load_dotenv()

ALCHEMY_API_KEY = os.getenv("ALCHEMY_API_KEY")
ALCHEMY_URL = f"https://eth-mainnet.g.alchemy.com/v2/{ALCHEMY_API_KEY}"

ENTRYPOINT_V06 = "0x5FF137D4b0FDCD49DcA30c7CF57E578a026d2789"
USEROP_EVENT_TOPIC = "0x49628fd1471006c1482da88028e9ce4dbb080b815c9b0344d39e5a8e6ec1419f"

def get_db():
    return psycopg2.connect(
        host=os.getenv("SUPABASE_HOST"),
        port=os.getenv("SUPABASE_PORT"),
        dbname=os.getenv("SUPABASE_DB"),
        user=os.getenv("SUPABASE_USER"),
        password=os.getenv("SUPABASE_PASSWORD")
    )

def rpc(method, params):
    r = requests.post(ALCHEMY_URL, json={
        "jsonrpc": "2.0", "method": method, "params": params, "id": 1
    })
    return r.json().get('result')

def get_latest_block():
    return int(rpc("eth_blockNumber", []), 16)

def get_bundler(tx_hash):
    tx = rpc("eth_getTransactionByHash", [tx_hash])
    return tx.get('from') if tx else None

last_block = get_latest_block() - 9
print("Collector started")

while True:
    try:
        latest = get_latest_block()
        from_block = last_block
        to_block = min(latest, from_block + 9)

        print(f"Checking blocks {from_block} to {to_block}...")

        logs = rpc("eth_getLogs", [{
            "fromBlock": hex(from_block),
            "toBlock": hex(to_block),
            "address": ENTRYPOINT_V06,
            "topics": [USEROP_EVENT_TOPIC]
        }])

        if logs:
            conn = get_db()
            cursor = conn.cursor()
            saved = 0

            for log in logs:
                userop_hash = log['topics'][1]
                sender = "0x" + log['topics'][2][-40:]
                paymaster = "0x" + log['topics'][3][-40:] if len(log['topics']) > 3 else None
                tx_hash = log['transactionHash']
                block_number = int(log['blockNumber'], 16)
                block_timestamp = int(log.get('blockTimestamp', '0x0'), 16)
                bundler = get_bundler(tx_hash)

                try:
                    cursor.execute("""
                        INSERT INTO userops
                        (userOpHash, transactionHash, sender, bundler,
                         paymaster, blockNumber, blockTimestamp, network)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                        ON CONFLICT (userOpHash) DO NOTHING
                    """, (userop_hash, tx_hash, sender, bundler,
                          paymaster, block_number, block_timestamp, 'mainnet'))
                    if cursor.rowcount == 1:
                        saved += 1
                except Exception as e:
                    print(f"Error saving: {e}")

            conn.commit()
            conn.close()
            print(f"Saved {saved} new UserOps to Supabase")
        else:
            print("No UserOps in this range")

        last_block = to_block + 1
        print("Waiting 2 minutes...")
        time.sleep(120)

    except Exception as e:
        print(f"Error: {e}")
        time.sleep(60)