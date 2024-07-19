# main.py

import os
import asyncio
from pytonapi import AsyncTonapi
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# TON API key (replace with your actual key)
TON_API_KEY = os.getenv('TON_API_KEY')

# Initialize TonAPI client
client = AsyncTonapi(key=7498773145:AAFbtAwryLpSjxWQxbmvm6pcSAWhToJDzRA)

async def find_account(address: str) -> None:
    """Find an account using TON API."""
    try:
        account = await client.account.get_info(address=address)
        print(f"Account found:\nAddress: {account.address}\nBalance: {account.balance}")
        if hasattr(account, 'interfaces') and account.interfaces:
            print("Interfaces:", ', '.join(account.interfaces))
    except Exception as e:
        print(f"Error finding account: {e}")

async def get_transactions(address: str, limit: int = 5) -> None:
    """Get recent transactions for an account."""
    try:
        transactions = await client.account.get_transactions(address=address, limit=limit)
        print(f"Recent transactions for {address}:")
        for tx in transactions:
            print(f"Hash: {tx.hash}")
            print(f"Time: {tx.utime}")
            print(f"Value: {tx.in_msg.value if tx.in_msg else 'N/A'}")
            print("---")
    except Exception as e:
        print(f"Error getting transactions: {e}")

async def main():
    """Main function to run the interactive CLI."""
    while True:
        print("\nTON API Bot")
        print("1. Find Account")
        print("2. Get Recent Transactions")
        print("3. Exit")
        
        choice = input("Enter your choice (1-3): ")
        
        if choice == '1':
            address = input("Enter the account address: ")
            await find_account(address)
        elif choice == '2':
            address = input("Enter the account address: ")
            limit = int(input("Enter the number of transactions to retrieve: "))
            await get_transactions(address, limit)
        elif choice == '3':
            print("Exiting...")
            break
        else:
            print("Invalid choice. Please try again.")

if __name__ == '__main__':
    asyncio.run(main())