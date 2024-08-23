import json
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, StaleElementReferenceException
from main import *


def delete_existing_bookmarks(driver, json_file):
    # Load existing bookmarks from JSON file
    try:
        with open(json_file, 'r', encoding='utf-8') as f:
            existing_bookmarks = json.load(f)
    except FileNotFoundError:
        print(f"JSON file {json_file} not found. No bookmarks will be deleted.")
        return
    
    existing_urls = set(bookmark['url'] for bookmark in existing_bookmarks)
    
    driver.get("https://twitter.com/i/bookmarks")
    
    deleted_count = 0
    while True:
        try:
            # Wait for tweets to load
            WebDriverWait(driver, 10).until(
                EC.presence_of_all_elements_located((By.CSS_SELECTOR, 'article[data-testid="tweet"]'))
            )
            
            # Find all tweets
            tweets = driver.find_elements(By.CSS_SELECTOR, 'article[data-testid="tweet"]')
            
            for tweet in tweets:
                try:
                    # Extract tweet URL
                    time_element = tweet.find_element(By.CSS_SELECTOR, 'time')
                    tweet_url = time_element.find_element(By.XPATH, '..').get_attribute('href')
                    
                    if tweet_url in existing_urls:
                        # Click the bookmark button to remove the bookmark
                        bookmark_button = tweet.find_element(By.CSS_SELECTOR, 'div[data-testid="bookmark"]')
                        bookmark_button.click()
                        deleted_count += 1
                        print(f"Deleted bookmark: {tweet_url}")
                except StaleElementReferenceException:
                    continue  # Skip this tweet if it becomes stale
                
            # Scroll down to load more tweets
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            
        except TimeoutException:
            print("No more tweets to load.")
            break
    
    print(f"Finished deleting bookmarks. Total deleted: {deleted_count}")

def main():
    driver = webdriver.Chrome()  # Make sure you have ChromeDriver installed and in PATH
    
    try:
        if login_to_twitter(driver):
            # Delete existing bookmarks first
            delete_existing_bookmarks(driver, 'twitter_bookmarks.json')
            
        else:
            print("Login failed. Unable to process bookmarks.")
    
    finally:
        driver.quit()

if __name__ == "__main__":
    main()