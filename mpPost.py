import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, WebDriverException, NoSuchElementException
import configparser
import time
import random
import string
from datetime import datetime

def load_config():
    config = configparser.ConfigParser()
    config.read('config.ini')
    return config['MINDS']

def setup_driver():
    try:
        options = uc.ChromeOptions()
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-gpu')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--start-maximized')
        driver = uc.Chrome(options=options)
        return driver
    except Exception as e:
        print(f"Error setting up WebDriver: {e}")
        return None

def login_to_minds(driver, config):
    try:
        print("Navigating to login page...")
        driver.get("https://www.minds.com/login")
        time.sleep(10)  # Increased wait time

        print("Current URL:", driver.current_url)
        print("Page title:", driver.title)

        # Check if we're already on the newsfeed page
        if "newsfeed" in driver.current_url:
            print("Already logged in and redirected to newsfeed.")
            return True

        # Use JavaScript to set values and click button
        js_script = """
        document.querySelector('input[name="username"]').value = arguments[0];
        document.querySelector('input[name="password"]').value = arguments[1];
        document.querySelector('button[type="submit"]').click();
        """
        driver.execute_script(js_script, config['username'], config['password'])
        print("Login script executed")

        # Wait for login to complete
        WebDriverWait(driver, 30).until(
            EC.url_contains("newsfeed")
        )
        print("Login successful")
        return True
    except TimeoutException as e:
        print(f"Timeout occurred: {e}")
    except Exception as e:
        print(f"An error occurred during login: {e}")
    
    print("Current URL:", driver.current_url)
    print("Page source:", driver.page_source[:1000])
    return False

def post_to_minds(driver, message):
    try:
        # Wait for the post input field to be visible
        post_field = WebDriverWait(driver, 30).until(
            EC.presence_of_element_located((By.XPATH, "//div[@contenteditable='true']"))
        )
        # Use JavaScript to set the post content
        driver.execute_script("arguments[0].innerHTML = arguments[1];", post_field, message)
        
        # Find and click the post button
        post_button = driver.find_element(By.XPATH, "//button[contains(text(), 'Post')]")
        post_button.click()
        
        # Wait for a success indicator (you might need to adjust this based on Minds' UI)
        WebDriverWait(driver, 30).until(
            EC.presence_of_element_located((By.XPATH, "//div[contains(text(), 'Posted')]"))
        )
        print("Successfully posted to Minds")
        return True
    except Exception as e:
        print(f"Failed to post. Error: {str(e)}")
        return False

def generate_sample_post():
    return f"This is a test post created at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}. " \
           f"Random string: {''.join(random.choices(string.ascii_letters + string.digits, k=10))}"

def main():
    config = load_config()
    
    driver = setup_driver()
    if not driver:
        print("Failed to set up WebDriver. Exiting.")
        return
    
    try:
        login_result = login_to_minds(driver, config)
        if login_result or "newsfeed" in driver.current_url:
            # Generate and post a sample message
            sample_message = generate_sample_post()
            print(f"Attempting to post: {sample_message}")
            success = post_to_minds(driver, sample_message)
            
            if success:
                print("Post operation completed successfully")
            else:
                print("Post operation failed")
        else:
            print("Login failed. Exiting.")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
    finally:
        print("Closing browser...")
        driver.quit()
        print("Browser closed.")

if __name__ == "__main__":
    main()