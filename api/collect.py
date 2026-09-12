from http.server import BaseHTTPRequestHandler
import requests
import psycopg2
import os

ALCHEMY_URL = f"https://eth-mainnet.g.alchemy.com/v2/{os.environ.get('ALCHEMY_API_KEY')}"
ENTRYPOINT_V06 = "0x5FF137D4b0FDCD49DcA30c7CF57E578a026d2789"
USEROP_EVENT_TOPIC = "0x49628fd1471006c1482da88028e9ce4dbb080b815c9b0344d39e5a8e6ec1419f"

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

def get_db():
    return psycopg2.connect(
        host=os.environ.get("SUPABASE_HOST"),
        port=os.environ.get("SUPABASE_PORT"),
        dbname=os.environ.get("SUPABASE_DB"),
        user=os.environ.get("SUPABASE_USER"),
        password=os.environ.get("SUPABASE_PASSWORD")
    )

class handler(BaseHTTPRequestHandler):
    def do_GET(self):
        try:
            latest = get_latest_block()
            from_block = latest - 9
            to_block = latest

            logs = rpc("eth_getLogs", [{
                "fromBlock": hex(from_block),
                "toBlock": hex(to_block),
                "address": ENTRYPOINT_V06,
                "topics": [USEROP_EVENT_TOPIC]
            }])

            saved = 0
            if logs:
                conn = get_db()
                cursor = conn.cursor()

                for log in logs:
                    userop_hash = log['topics'][1]
                    sender = "0x" + log['topics'][2][-40:]
                    paymaster = "0x" + log['topics'][3][-40:] if len(log['topics']) > 3 else None
                    tx_hash = log['transactionHash']
                    block_number = int(log['blockNumber'], 16)
                    block_timestamp = int(log.get('blockTimestamp', '0x0'), 16)
                    bundler = get_bundler(tx_hash)

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

                conn.commit()
                conn.close()

            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(f'{{"saved": {saved}}}'.encode())

        except Exception as e:
            self.send_response(500)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(f'{{"error": "{str(e)}"}}'.encode())