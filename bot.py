import asyncio
from web3 import Web3
import logging
import json
import signal
import sys
import time
from decimal import Decimal
from ens import ENS

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Replace with your Ethereum node URL (e.g., Infura)
ETH_NODE_URL = "https://mainnet.infura.io/v3/9b4e315a936e4964b7ac46cce53ad5bf"

# Initialize Web3
w3 = Web3(Web3.HTTPProvider(ETH_NODE_URL))
ns = ENS.from_web3(w3)

# Replace with your Telegram bot token and chat ID
TELEGRAM_BOT_TOKEN = "147e42c9d5ba889829ac864e99d370b6"
TELEGRAM_CHAT_ID = "tgg0hstBot"

# Global list to store transaction data
transactions = []

def signal_handler(sig, frame):
    logger.info("Ctrl+C detected. Saving data and exiting...")
    save_data()
    sys.exit(0)

def decimal_default(obj):
    if isinstance(obj, Decimal):
        return float(obj)
    raise TypeError

def save_data():
    filename = f"mempool_data_{int(time.time())}.json"
    with open(filename, 'w') as f:
        json.dump(transactions, f, default=decimal_default)
    logger.info(f"Data saved to {filename}")

def get_ens_name(address):
    try:
        return ns.name(address)
    except Exception:
        return None

async def monitor_mempool():
    global transactions
    while True:
        try:
            pending_block = w3.eth.get_block('pending', full_transactions=True)
            pending_tx_count = len(pending_block.transactions)
            logger.info(f"Number of pending transactions: {pending_tx_count}")

            for tx in pending_block.transactions:
                from_ens = get_ens_name(tx['from'])
                to_ens = get_ens_name(tx['to']) if tx['to'] else None
                
                tx_data = {
                    "hash": tx['hash'].hex(),
                    "from": tx['from'],
                    "from_ens": from_ens,
                    "to": tx['to'],
                    "to_ens": to_ens,
                    "value": float(w3.from_wei(tx['value'], 'ether')),
                    "gas": tx['gas'],
                    "gasPrice": float(w3.from_wei(tx['gasPrice'], 'gwei')),
                    "nonce": tx['nonce']
                }
                transactions.append(tx_data)
                logger.info(f"Recorded transaction: {tx_data['hash']} | From: {from_ens or tx['from']} | To: {to_ens or tx['to']}")


            await asyncio.sleep(10)
        except Exception as e:
            logger.error(f"An error occurred: {e}")
            await asyncio.sleep(30)

# Main asynchronous function
async def main():
    if not w3.is_connected():
        logger.error("Failed to connect to Ethereum node")
        return
    logger.info("Successfully connected to Ethereum node")
    await monitor_mempool()

if __name__ == "__main__":
    signal.signal(signal.SIGINT, signal_handler)
    asyncio.run(main())

    
    # Run the main asynchronous function
    asyncio.run(main())