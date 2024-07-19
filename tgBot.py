import asyncio
import aioschedule as schedule
import time
import random
import json
import os
import getpass
import re
from datetime import datetime, timedelta
from telethon import TelegramClient, events
from telethon.errors import SessionPasswordNeededError, PhoneCodeInvalidError, SendCodeUnavailableError
from telethon.sessions import StringSession

# Configuration settings
API_ID = '29358263'  # Replace with your API ID from my.telegram.org
API_HASH = '147e42c9d5ba889829ac864e99d370b6'  # Replace with your API Hash from my.telegram.org
PHONE_NUMBER = '+19862697290'  # Include country code, e.g., '+12345678900'
TARGET_USERNAME = 'UnitonAIBot'  # Replace with the actual username of the bot
REPLY_TO_MESSAGE_ID = None  # Will be set when finding the message to reply to
JSON_FILE = 'long_tweets.json'  # Update this line

# Global variables
messages = []
client = None
loop = asyncio.get_event_loop()

def truncate_message(message, max_length=4096):
    """Truncate message to fit Telegram's limit."""
    if len(message) > max_length:
        return message[:max_length-3] + "..."
    return message

def load_messages():
    """Load messages from JSON file and clean up the data."""
    global messages
    if os.path.exists(JSON_FILE):
        with open(JSON_FILE, 'r') as f:
            content = f.read()
        try:
            # Remove any lines containing unwanted content
            cleaned_content = '\n'.join(line for line in content.split('\n') 
                                        if not any(word in line.lower() for word in ["mint", "subscribe"]))
            
            # Try to parse the cleaned content
            parsed_data = json.loads(cleaned_content)
            
            # Extract only the relevant message data
            messages = []
            for item in parsed_data:
                if isinstance(item, dict) and 'content' in item:
                    messages.append({'content': item['content'].replace('\\n', '\n')})
            
            print(f"Loaded and cleaned {len(messages)} messages from {JSON_FILE}")
        except json.JSONDecodeError as e:
            print(f"JSON decode error: {str(e)}")
            print("Problematic part of the JSON:")
            start = max(0, e.pos - 50)
            end = min(len(cleaned_content), e.pos + 50)
            print(cleaned_content[start:end])
            return
    else:
        print(f"No existing messages file found at {JSON_FILE}")
        recreate_json_file()
        load_messages()  # Recursively call to load the newly created file

def save_messages():
    """Save messages to JSON file."""
    messages_to_save = [{'content': msg['content'].replace('\n', '\\n')} for msg in messages]
    with open(JSON_FILE, 'w') as f:
        json.dump(messages_to_save, f, indent=2)
    print(f"Saved {len(messages)} messages to {JSON_FILE}")

def recreate_json_file():
    """Recreate the JSON file with proper formatting."""
    dummy_messages = [
        {"content": "This is a test message."},
        {"content": "This is another test message."}
    ]
    with open(JSON_FILE, 'w') as f:
        json.dump(dummy_messages, f, indent=2)
    print(f"Recreated {JSON_FILE} with dummy messages.")

async def find_reply_message():
    """Find the message to reply to in the chat history."""
    global REPLY_TO_MESSAGE_ID
    search_text = input("Enter a unique part of the message you want to reply to: ")
    print(f"Searching for messages containing: '{search_text}'")
    
    message_count = 0
    async for message in client.iter_messages(TARGET_USERNAME, limit=100):  # Limit to last 100 messages
        message_count += 1
        if message.text and search_text.lower() in message.text.lower():
            REPLY_TO_MESSAGE_ID = message.id
            print(f"Found message to reply to. ID: {REPLY_TO_MESSAGE_ID}")
            print(f"Message text: {message.text[:50]}...")  # Print first 50 characters
            return
    
    print(f"Couldn't find any messages containing '{search_text}'.")
    print(f"Searched through {message_count} messages.")
    print("Make sure you're searching for text that's actually in the message.")
    print("You might need to send a message to the bot first if there's no chat history.")

async def async_send_random_message():
    """Send a random message from the loaded messages."""
    global client
    if messages and REPLY_TO_MESSAGE_ID:
        message_dict = random.choice(messages)
        if isinstance(message_dict, dict) and 'content' in message_dict:
            message = message_dict['content']
        else:
            message = str(message_dict)  # fallback in case the structure is unexpected
        
        # Add line breaks between sentences
        message = re.sub(r'(?<!\n)(?<=\.|\?|\!)\s+', '\n\n', message)
        
        truncated_message = truncate_message(message)
        try:
            await client.send_message(TARGET_USERNAME, truncated_message, reply_to=REPLY_TO_MESSAGE_ID)
            print(f"Sent message: {truncated_message[:50]}...")
        except Exception as e:
            print(f"Failed to send message: {e}")
    elif not REPLY_TO_MESSAGE_ID:
        print("No message to reply to. Run 'Find reply message' first.")
    else:
        print("No messages available to send. Please add some messages first.")

def run_async_send_random_message():
    asyncio.create_task(async_send_random_message())

def schedule_posts():
    """Schedule 6 random posts throughout the day."""
    schedule.clear()
    now = datetime.now()
    post_times = sorted([now + timedelta(seconds=random.randint(1, 86400)) for _ in range(6)])
    for t in post_times:
        schedule.every().day.at(t.strftime("%H:%M")).do(run_async_send_random_message)
        print(f"Scheduled post for {t.strftime('%H:%M')}")
    print("Scheduled 6 posts for today")

async def main_loop():
    """Main loop for running the bot."""
    print("Sending initial message...")
    await async_send_random_message()
    print("Starting main loop. Press Ctrl+C to stop.")
    while True:
        schedule.run_pending()
        await asyncio.sleep(1)

async def initialize_client():
    global client
    if client and client.is_connected():
        return True
    
    try:
        session_file = 'telegram_session.txt'
        if os.path.exists(session_file):
            with open(session_file, 'r') as f:
                session_string = f.read()
        else:
            session_string = ''

        client = TelegramClient(StringSession(session_string), API_ID, API_HASH, loop=loop)
        
        print("Attempting to connect to Telegram...")
        await client.connect()
        
        if not await client.is_user_authorized():
            print(f"Sending code to {PHONE_NUMBER}...")
            await client.send_code_request(PHONE_NUMBER)
            
            while True:
                try:
                    code = input("Please enter the code you received: ")
                    await client.sign_in(PHONE_NUMBER, code)
                    break
                except PhoneCodeInvalidError:
                    print("Invalid code. Please try again.")
                except SessionPasswordNeededError:
                    password = getpass.getpass("Two-step verification is enabled. Please enter your password: ")
                    await client.sign_in(password=password)
                    break
                except SendCodeUnavailableError:
                    print("Too many attempts. Please wait for a while before trying again.")
                    return False
        
        with open(session_file, 'w') as f:
            f.write(client.session.save())
        
        print("Successfully connected to Telegram!")
        return True
    except Exception as e:
        print(f"An error occurred during client initialization: {str(e)}")
        return False

async def interactive_menu():
    """Provide an interactive menu for user operations."""
    while True:
        print("\n--- Telegram Bot Menu ---")
        print("1. Add message")
        print("2. View messages")
        print("3. Delete message")
        print("4. Find reply message")
        print("5. Start bot")
        print("6. Exit")
        choice = input("Enter your choice (1-6): ")

        if choice == '1':
            message = get_multiline_input()
            if len(message) > 4096:
                print("Warning: Message exceeds Telegram's 4096 character limit. It will be truncated when sent.")
            messages.append({'content': message})
            save_messages()
            print("Message added successfully.")
        elif choice == '2':
            if messages:
                print(f"Total messages: {len(messages)}")
                for i, msg in enumerate(messages, 1):
                    print(f"Message {i}:")
                    if isinstance(msg, dict):
                        for key, value in msg.items():
                            print(f"  {key}: {value[:200]}..." if len(str(value)) > 200 else f"  {key}: {value}")
                    else:
                        print(f"  {msg[:200]}..." if len(str(msg)) > 200 else f"  {msg}")
                    print()  # Add an extra line between messages for readability
            else:
                print("No messages available.")
            input("Press Enter to continue...")  # Wait for user input before returning to menu
        elif choice == '3':
            if messages:
                for i, msg in enumerate(messages, 1):
                    if isinstance(msg, dict) and 'content' in msg:
                        content = msg['content']
                    else:
                        content = str(msg)
                    print(f"{i}. {content[:50]}..." if len(content) > 50 else f"{i}. {content}")
                try:
                    index = int(input("Enter message number to delete: ")) - 1
                    if 0 <= index < len(messages):
                        deleted_message = messages.pop(index)
                        save_messages()
                        print(f"Deleted message: {str(deleted_message)[:50]}...")
                    else:
                        print("Invalid message number.")
                except ValueError:
                    print("Please enter a valid number.")
            else:
                print("No messages available to delete.")
        elif choice == '4':
            await find_reply_message()
            if not REPLY_TO_MESSAGE_ID:
                print("Would you like to try searching again? (y/n)")
                retry = input().lower()
                while retry == 'y':
                    await find_reply_message()
                    if REPLY_TO_MESSAGE_ID:
                        break
                    print("Would you like to try searching again? (y/n)")
                    retry = input().lower()
        elif choice == '5':
            if not REPLY_TO_MESSAGE_ID:
                print("Please find the reply message first (option 4)")
            elif not messages:
                print("Please add some messages first (option 1)")
            else:
                schedule_posts()
                print("Bot is starting...")
                try:
                    await main_loop()
                except KeyboardInterrupt:
                    print("\nBot stopped by user.")
        elif choice == '6':
            print("Exiting the program. Goodbye!")
            break
        else:
            print("Invalid choice. Please enter a number between 1 and 6.")

def get_multiline_input():
    """Get multi-line input from the user."""
    print("Enter your message (type '\\end' on a new line to finish):")
    lines = []
    while True:
        line = input()
        if line.strip() == '\\end':
            break
        lines.append(line)
    return '\n'.join(lines)

async def main():
    print("Starting Telegram Bot Application")
    print("Loading messages...")
    if not os.path.exists(JSON_FILE):
        recreate_json_file()
    load_messages()
    
    if await initialize_client():
        print("Entering interactive menu...")
        await interactive_menu()
    else:
        print("Failed to initialize Telegram client. Exiting...")
    
    print("Application terminated.")

if __name__ == "__main__":
    asyncio.run(main())