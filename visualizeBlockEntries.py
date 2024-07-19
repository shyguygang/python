import requests
import time
import json
import mysql.connector
import logging
from datetime import datetime, timedelta
from collections import defaultdict
import sys

# Set up logging
logging.basicConfig(filename='user_activity_monitor.log', level=logging.INFO,
                    format='%(asctime)s - %(levelname)s - %(message)s')

# Also log to console
console = logging.StreamHandler()
console.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
console.setFormatter(formatter)
logging.getLogger('').addHandler(console)

# DeSo Node URL - Change this to your preferred node
DESO_API_URL = "http://localhost:3000/api/v0"
logging.info(f"Using DeSo node URL: {DESO_API_URL}")

USERS = [
    "BC1YLhtBTFXAsKZgoaoYNW8mWAJWdfQjycheAeYjaX46azVrnZfJ94s",  # Sharkgang
    "BC1YLgCcsEwFHK4vBRgduUAn8c9Qxh8meoGWV2zsTHoyacS8w6uBp3i",  # nader
    "BC1YLhaPJwqt6R6cZK8CoMnVDGbfUg8Yr8VPVEGf5ZbwGLzQfYs5xhm",  # amurloc
    "BC1YLfunDRhQVvj5WXoKTXp1wSNbNHRVAHXxL7eDH7T3FU2ZHEKcVcR",  # tangyshroom
    "BC1YLgGmcTmyBNcFXyHk9RuEexmSLjrbxWxzVZQPH3PQVmUDhVS8kGz",  # valtran
]

# MySQL Database Configuration
DB_CONFIG = {
    'host': 'localhost',
    'user': 'your_username',
    'password': 'your_password',
    'database': 'deso_activity'
}

def get_db_connection():
    try:
        conn = mysql.connector.connect(**DB_CONFIG)
        return conn
    except mysql.connector.Error as err:
        logging.error(f"Error connecting to MySQL database: {err}")
        sys.exit(1)

conn = get_db_connection()
c = conn.cursor(buffered=True)

def initialize_database():
    try:
        c.execute('''CREATE TABLE IF NOT EXISTS activities
                     (id INT AUTO_INCREMENT PRIMARY KEY,
                      user VARCHAR(255),
                      timestamp DATETIME,
                      tx_type VARCHAR(255),
                      details LONGTEXT,
                      notification_type VARCHAR(255),
                      interacted_with VARCHAR(255),
                      estimated_session_start DATETIME,
                      estimated_session_duration INT,
                      interaction_details LONGTEXT)''')
        
        c.execute('''CREATE TABLE IF NOT EXISTS last_transaction_heights
                     (user VARCHAR(255) PRIMARY KEY,
                      height INT)''')
        
        # Create indexes
        c.execute("CREATE INDEX IF NOT EXISTS idx_user ON activities(user)")
        c.execute("CREATE INDEX IF NOT EXISTS idx_timestamp ON activities(timestamp)")
        c.execute("CREATE INDEX IF NOT EXISTS idx_notification_type ON activities(notification_type)")
        
        conn.commit()
        logging.info("Database initialization complete")
    except mysql.connector.Error as err:
        logging.error(f"Error initializing database: {err}")
        sys.exit(1)

initialize_database()

def fetch_transactions(user_public_key, last_height=0):
    try:
        endpoint = f"{DESO_API_URL}/get-transactions-for-user"
        params = {
            "PublicKeyBase58Check": user_public_key,
            "Limit": 20,
            "LastTransactionHeight": last_height
        }
        response = requests.get(endpoint, params=params, timeout=10)
        response.raise_for_status()
        return response.json()['Transactions']
    except requests.RequestException as e:
        logging.error(f"Error fetching transactions for {user_public_key}: {str(e)}")
        return []

def estimate_session_data(user, timestamp):
    try:
        c.execute("""
            SELECT timestamp FROM activities
            WHERE user = %s AND timestamp < %s
            ORDER BY timestamp DESC
            LIMIT 1
        """, (user, timestamp))
        last_activity = c.fetchone()
        
        if last_activity:
            last_timestamp = last_activity[0]
            current_timestamp = datetime.strptime(timestamp, '%Y-%m-%d %H:%M:%S')
            time_diff = (current_timestamp - last_timestamp).total_seconds()
            
            if time_diff < 3600:  # If less than an hour has passed, consider it the same session
                return last_timestamp.strftime('%Y-%m-%d %H:%M:%S'), int(time_diff)
            
        return timestamp, 0  # New session
    except mysql.connector.Error as err:
        logging.error(f"Database error in estimate_session_data: {err}")
        return timestamp, 0

def process_transaction(user, transaction):
    try:
        tx_type = transaction['TransactionType']
        timestamp = datetime.fromtimestamp(transaction['TransactionMetadata']['TxnIndexInBlock']).strftime('%Y-%m-%d %H:%M:%S')
        details = json.dumps(transaction)

        interacted_with = None
        notification_type = 'other'
        interaction_details = {}

        if tx_type == 'SUBMIT_POST':
            notification_type = 'post'
            interacted_with = 'public'
            interaction_details['post_hash'] = transaction.get('PostHashHex')
            interaction_details['post_text'] = transaction.get('Body', '')[:100]
            interaction_details['mentions'] = transaction.get('MentionedPublicKeys', [])
        elif tx_type == 'FOLLOW':
            notification_type = 'follow'
            interacted_with = transaction.get('FollowedPublicKey')
            interaction_details['is_unfollow'] = transaction.get('IsUnfollow')
        elif tx_type == 'BASIC_TRANSFER':
            notification_type = 'transfer'
            interacted_with = transaction.get('RecipientPublicKey')
            interaction_details['amount_nanos'] = transaction.get('AmountNanos')
        elif tx_type == 'LIKE':
            notification_type = 'like'
            interacted_with = transaction.get('LikedPostHash')
            interaction_details['is_unlike'] = transaction.get('IsUnlike')
        elif tx_type == 'PRIVATE_MESSAGE':
            notification_type = 'message'
            interacted_with = transaction.get('RecipientPublicKey')
            interaction_details['message_length'] = len(transaction.get('EncryptedMessageText', ''))
        elif tx_type == 'CREATOR_COIN':
            notification_type = 'creator_coin'
            interacted_with = transaction.get('CreatorPublicKeyBase58Check')
            interaction_details['operation_type'] = transaction.get('OperationType')
            interaction_details['desonanos_to_sell'] = transaction.get('DeSoToSellNanos')

        estimated_session_start, estimated_session_duration = estimate_session_data(user, timestamp)

        c.execute("""
            INSERT INTO activities 
            (user, timestamp, tx_type, details, notification_type, interacted_with, 
             estimated_session_start, estimated_session_duration, interaction_details)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (user, timestamp, tx_type, details, notification_type, interacted_with,
              estimated_session_start, estimated_session_duration, json.dumps(interaction_details)))
        conn.commit()

        logging.info(f"User: {user}")
        logging.info(f"Processed {tx_type} transaction at {timestamp}")
        logging.info(f"Notification type: {notification_type}")
        logging.info(f"Interacted with: {interacted_with}")
        logging.info(f"Estimated session start: {estimated_session_start}")
        logging.info(f"Estimated session duration: {estimated_session_duration} seconds")
        logging.info(f"Interaction details: {interaction_details}")
        logging.info("---")

    except mysql.connector.Error as err:
        logging.error(f"Database error in process_transaction: {err}")
    except Exception as e:
        logging.error(f"Error processing transaction: {str(e)}")

def get_last_transaction_height(user):
    try:
        c.execute("SELECT height FROM last_transaction_heights WHERE user = %s", (user,))
        result = c.fetchone()
        return result[0] if result else 0
    except mysql.connector.Error as err:
        logging.error(f"Database error in get_last_transaction_height: {err}")
        return 0

def update_last_transaction_height(user, height):
    try:
        c.execute("""
            INSERT INTO last_transaction_heights (user, height)
            VALUES (%s, %s)
            ON DUPLICATE KEY UPDATE height = %s
        """, (user, height, height))
        conn.commit()
    except mysql.connector.Error as err:
        logging.error(f"Database error in update_last_transaction_height: {err}")

def analyze_user_behavior(user):
    try:
        c.execute("""
            SELECT notification_type, interacted_with, estimated_session_duration, interaction_details
            FROM activities
            WHERE user = %s
            ORDER BY timestamp DESC
            LIMIT 1000
        """, (user,))
        activities = c.fetchall()

        interaction_count = defaultdict(int)
        session_durations = []
        interaction_patterns = defaultdict(list)

        for activity in activities:
            notification_type, interacted_with, session_duration, interaction_details = activity
            interaction_count[notification_type] += 1
            if session_duration > 0:
                session_durations.append(session_duration)
            
            details = json.loads(interaction_details)
            if notification_type == 'post':
                interaction_patterns['mentions'].extend(details.get('mentions', []))
            elif notification_type == 'creator_coin':
                interaction_patterns['creator_coin_operations'].append(details.get('operation_type'))

        logging.info(f"\nAnalysis for user {user}:")
        logging.info(f"Interaction distribution: {dict(interaction_count)}")
        logging.info(f"Average session duration: {sum(session_durations) / len(session_durations) if session_durations else 0:.2f} seconds")
        logging.info(f"Most mentioned users: {sorted(interaction_patterns['mentions'], key=interaction_patterns['mentions'].count, reverse=True)[:5]}")
        logging.info(f"Creator coin operations: {interaction_patterns['creator_coin_operations']}")
    except mysql.connector.Error as err:
        logging.error(f"Database error in analyze_user_behavior: {err}")
    except Exception as e:
        logging.error(f"Error analyzing user behavior: {str(e)}")

def fetch_initial_data():
    for user in USERS:
        logging.info(f"\nFetching initial transactions for user: {user}")
        transactions = fetch_transactions(user)
        for tx in transactions:
            process_transaction(user, tx)
        if transactions:
            update_last_transaction_height(user, transactions[0]['TransactionMetadata']['TxnIndexInBlock'])
        analyze_user_behavior(user)

def monitor_new_transactions():
    while True:
        try:
            for user in USERS:
                last_height = get_last_transaction_height(user)
                logging.info(f"\nChecking new transactions for user: {user}")
                transactions = fetch_transactions(user, last_height)
                for tx in transactions:
                    process_transaction(user, tx)
                if transactions:
                    update_last_transaction_height(user, transactions[0]['TransactionMetadata']['TxnIndexInBlock'])
                analyze_user_behavior(user)
            
            logging.info("\nWaiting for 60 seconds before next check...")
            time.sleep(60)  # Wait for 60 seconds before checking again
        except Exception as e:
            logging.error(f"Error in monitor_new_transactions: {str(e)}")
            time.sleep(60)  # Wait before retrying

def main():
    try:
        fetch_initial_data()
        monitor_new_transactions()
    except KeyboardInterrupt:
        logging.info("\nMonitoring stopped.")
    except Exception as e:
        logging.error(f"Unexpected error in main loop: {str(e)}")
    finally:
        c.close()
        conn.close()

if __name__ == "__main__":
    main()