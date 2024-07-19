from selenium import webdriver
from selenium.webdriver.firefox.service import Service as FirefoxService
from selenium.webdriver.firefox.options import Options as FirefoxOptions
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.firefox import GeckoDriverManager
import json
import time

def setup_driver():
    firefox_options = FirefoxOptions()
    firefox_options.add_argument("--headless")
    service = FirefoxService(GeckoDriverManager().install())
    return webdriver.Firefox(service=service, options=firefox_options)

def get_post_urls(driver, base_url):
    print(f"Getting post URLs from {base_url}")
    driver.get(base_url)
    WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.TAG_NAME, "body")))
    post_links = driver.find_elements(By.CSS_SELECTOR, f"a[href^='{base_url}/']")
    urls = [link.get_attribute('href') for link in post_links if link.get_attribute('href').count('/') == 4]
    return list(dict.fromkeys(urls))  # Remove duplicates

def extract_content(driver, url):
    print(f"Extracting content from: {url}")
    driver.get(url)
    WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.TAG_NAME, "body")))
    
    # Find the main text content
    main_content = driver.find_element(By.TAG_NAME, "body").text
    
    return {
        "url": url,
        "content": main_content,
        "author": "kingbook.eth"
    }

def scrape_mirror_xyz(base_url):
    driver = setup_driver()
    try:
        post_urls = get_post_urls(driver, base_url)
        print(f"Found {len(post_urls)} posts to scrape")

        scraped_data = []
        for index, url in enumerate(post_urls, 1):
            print(f"Scraping post {index}/{len(post_urls)}: {url}")
            content = extract_content(driver, url)
            scraped_data.append(content)
            time.sleep(2)  # Be respectful with requests
    finally:
        driver.quit()
    return scraped_data

def main():
    default_url = "https://mirror.xyz/kingbook.eth"
    base_url = input(f"Enter the Mirror.xyz base URL (press Enter for {default_url}): ") or default_url
    
    print("Scraping, please wait...")
    scraped_data = scrape_mirror_xyz(base_url)
    
    if scraped_data:
        filename = "mirror_xyz_data.json"
        with open(filename, "w", encoding='utf-8') as f:
            json.dump(scraped_data, f, ensure_ascii=False, indent=2)
        print(f"Data saved to {filename}")
        print(f"Number of posts scraped: {len(scraped_data)}")
    else:
        print("No data was scraped. Please check the URL and try again.")

if __name__ == "__main__":
    main()