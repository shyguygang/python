import requests
import time
from desoapi import DeSoApi

# Initialize DeSo API with your public key
public_key = "BC1YLgxr4MHqWPegTm2vKw4Qp3FEvr7p2rjxWZUYWaDHLsXUHdw8DCf"
deso_api = DeSoApi(public_key)

# Function to get recent posts
def get_recent_posts(num_posts=10):
    endpoint = "https://node.deso.org/api/v0/get-posts-stateless"
    payload = {
        "NumToFetch": num_posts,
        "OrderBy": "newest",
        "ReaderPublicKeyBase58Check": public_key
    }
    response = requests.post(endpoint, json=payload)
    return response.json()["PostsFound"]

# Function to repost
def repost(post_hash):
    try:
        response = deso_api.create_repost(post_hash)
        print(f"Reposted: {post_hash}")
        return response
    except Exception as e:
        print(f"Error reposting {post_hash}: {str(e)}")
        return None

# Main bot loop
def run_bot():
    while True:
        posts = get_recent_posts()
        for post in posts:
            repost(post["PostHashHex"])
        time.sleep(600)  # Wait 10 minutes before next batch

if __name__ == "__main__":
    run_bot()