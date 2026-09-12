import requests
import os
from dotenv import load_dotenv

# This reads your .env file and loads the API key into memory
load_dotenv()
api_key = os.getenv("PIMLICO_API_KEY")

# This is the URL of Pimlico's bundler
# 1 = Ethereum mainnet's chain ID
url = f"https://api.pimlico.io/v2/1/rpc?apikey={api_key}"

# This is the "question" we're sending — asking for current gas price
payload = {
    "jsonrpc": "2.0",
    "method": "pimlico_getUserOperationGasPrice",
    "params": [],
    "id": 1
}

# Send the request and store the response
response = requests.post(url, json=payload)

# Print what came back
print(response.json())