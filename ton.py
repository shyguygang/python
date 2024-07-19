import requests
import json

class TONPoster:
    def __init__(self, api_key):
        self.api_key = api_key
        self.base_url = "https://api.ton.org/v1"  # Replace with the actual TON API base URL

    def post_message(self, message):
        endpoint = f"{self.base_url}/send-message"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        payload = {
            "message": message
        }

        response = requests.post(endpoint, headers=headers, data=json.dumps(payload))
        
        if response.status_code == 200:
            return {"success": True, "response": response.json()}
        else:
            return {"success": False, "error": response.text}

class MultiPlatformPoster:
    def __init__(self):
        self.platforms = {}

    def add_platform(self, name, poster):
        self.platforms[name] = poster

    def post_to_all(self, message):
        results = {}
        for platform, poster in self.platforms.items():
            results[platform] = poster.post_message(message)
        return results

# Usage
if __name__ == "__main__":
    ton_api_key = "your_ton_api_key_here"
    
    ton_poster = TONPoster(ton_api_key)
    
    multi_poster = MultiPlatformPoster()
    multi_poster.add_platform("TON", ton_poster)
    
    message = "Hello, this is a test message from our multi-platform bot!"
    results = multi_poster.post_to_all(message)
    
    print(json.dumps(results, indent=2))