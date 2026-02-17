import os
import time
import requests
from web3 import Web3
from eth_utils import to_bytes

# ==========================
# CONFIGURATION
# ==========================
AGENT_ID = 16662  # agent kamu
RPC_URL = "https://mainnet.base.org"  # Base Mainnet RPC

# Alamat ProblemManager resmi AgentCoin
PROBLEM_MANAGER_ADDRESS = Web3.to_checksum_address("0x7D563ae2881D2fC72f5f4c66334c079B4Cc051c6")

# PRIVATE_KEY dari Railway Environment Variable
PRIVATE_KEY = os.getenv("PRIVATE_KEY")
if not PRIVATE_KEY:
    raise Exception("Set PRIVATE_KEY di Railway Environment Variables")

# ==========================
# CONNECT TO BLOCKCHAIN
# ==========================
w3 = Web3(Web3.HTTPProvider(RPC_URL))
account = w3.eth.account.from_key(PRIVATE_KEY)
address = account.address
print("Using wallet:", address)

# Minimal ABI untuk submitAnswer
PROBLEM_MANAGER_ABI = [
    {
        "inputs": [
            {"internalType": "uint256","name":"problemId","type":"uint256"},
            {"internalType": "bytes32","name":"answer","type":"bytes32"}
        ],
        "name":"submitAnswer",
        "outputs":[],
        "stateMutability":"nonpayable",
        "type":"function"
    }
]

contract = w3.eth.contract(address=PROBLEM_MANAGER_ADDRESS, abi=PROBLEM_MANAGER_ABI)

# REST API endpoint untuk problem
API_URL = "https://agentcoin.site/api/problem/current"

# ==========================
# FUNCTION TO SOLVE PROBLEM
# ==========================
def solve_problem(N):
    """Sum integers ≤ N divisible by 3 or 5 but not divisible by 15, modulo (N mod 100 + 1)"""
    total = sum(k for k in range(1, N+1) if (k%3==0 or k%5==0) and k%15!=0)
    mod = (N % 100) + 1
    return total % mod

# ==========================
# SUBMIT ANSWER
# ==========================
def submit_answer(problem_id, answer_int):
    # Fix Web3.toBytes error by using eth_utils.to_bytes
    answer_bytes32 = to_bytes(answer_int).rjust(32, b'\0')
    tx = contract.functions.submitAnswer(problem_id, answer_bytes32).buildTransaction({
        "from": address,
        "nonce": w3.eth.get_transaction_count(address),
        "gas": 300000,
        "gasPrice": w3.eth.gas_price
    })
    signed_tx = w3.eth.account.sign_transaction(tx, private_key=PRIVATE_KEY)
    tx_hash = w3.eth.send_raw_transaction(signed_tx.rawTransaction)
    print("Submitted tx:", tx_hash.hex())
    receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
    print("Tx confirmed:", receipt.status)

# ==========================
# MAIN LOOP
# ==========================
def main():
    print("Starting Auto Mining for Agent ID", AGENT_ID)

    while True:
        try:
            # Fetch problem
            resp = requests.get(API_URL, timeout=10)
            if resp.status_code != 200:
                print("Cannot fetch problem, status:", resp.status_code)
                time.sleep(10)
                continue

            data = resp.json()
            if not data.get("is_active", False):
                print("No active problem, waiting...")
                time.sleep(10)
                continue

            problem_id = data["problem_id"]
            print("Problem found:", problem_id)

            # Solve
            answer = solve_problem(AGENT_ID)
            print("Calculated answer:", answer)

            # Submit
            submit_answer(problem_id, answer)
            print("Sleeping 5 minutes before next poll...")
            time.sleep(300)

        except Exception as e:
            print("Error:", e)
            time.sleep(10)

if __name__ == "__main__":
    main()
