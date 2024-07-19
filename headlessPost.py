from selenium import webdriver
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.keys import Keys
import time

def initialize_driver():
    firefox_options = Options()
    driver = webdriver.Firefox(options=firefox_options)
    return driver

def login(driver):
    driver.get("https://twitter.com/i/flow/login")
    
    try:
        # Wait for the login page to load
        WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.XPATH, "//input[@autocomplete='username']"))
        )
        print("Login page loaded. Please log in manually and complete 2FA if required.")
        input("Press Enter once you've successfully logged in...")
        
        # Wait for home page to load
        WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.XPATH, "//div[@data-testid='primaryColumn']"))
        )
        print("Successfully logged in.")
    except Exception as e:
        print(f"An error occurred during login: {str(e)}")

def post_tweet(driver, message):
    try:
        # Wait for the tweet button and click it
        tweet_button = WebDriverWait(driver, 20).until(
            EC.element_to_be_clickable((By.XPATH, "//a[@data-testid='SideNav_NewTweet_Button']"))
        )
        tweet_button.click()

        # Wait for the tweet textarea and enter the message
        tweet_input = WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.XPATH, "//div[@data-testid='tweetTextarea_0']"))
        )
        tweet_input.send_keys(message)

        # Click the tweet button to post
        post_button = WebDriverWait(driver, 20).until(
            EC.element_to_be_clickable((By.XPATH, "//div[@data-testid='tweetButtonInline']"))
        )
        post_button.click()

        print(f"Successfully posted: {message}")
        time.sleep(5)  # Wait for the tweet to be posted
    except Exception as e:
        print(f"An error occurred while posting: {str(e)}")

def main():
    driver = initialize_driver()
    
    login(driver)
    
    while True:
        message = input("Enter your tweet (or 'quit' to exit): ")
        if message.lower() == 'quit':
            break
        post_tweet(driver, message)
    
    driver.quit()

if __name__ == "__main__":
    main()