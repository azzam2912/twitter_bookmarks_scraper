from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
import time
import json
import os

def login_to_twitter(driver):
    driver.get("https://twitter.com/login")
    
    print("Please log in manually in the browser window.")
    print("After logging in, navigate to your Twitter homepage.")
    input("Press Enter when you've successfully logged in and are on the Twitter homepage...")
    
    # Wait for the home timeline to ensure we're logged in
    try:
        WebDriverWait(driver, 30).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, 'div[data-testid="primaryColumn"]'))
        )
        print("Login confirmed. Proceeding with scraping...")
    except TimeoutException:
        print("Timed out waiting for the home page to load. Please ensure you're logged in and on the Twitter homepage.")
        return False
    
    return True

def scrape_bookmarks(driver, max_posts=500, scroll_pause_time=2):
    driver.get("https://twitter.com/i/bookmarks")
    
    bookmarks = []
    last_height = driver.execute_script("return document.body.scrollHeight")
    
    while len(bookmarks) < max_posts:
        # Scroll down to bottom
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        
        # Wait to load page
        time.sleep(scroll_pause_time)
        
        # Extract bookmarks
        tweets = driver.find_elements(By.CSS_SELECTOR, 'article[data-testid="tweet"]')
        for tweet in tweets:
            if len(bookmarks) >= max_posts:
                break
            try:
                author = tweet.find_element(By.CSS_SELECTOR, 'div[data-testid="User-Name"]').text
                content = tweet.find_element(By.CSS_SELECTOR, 'div[data-testid="tweetText"]').text
                
                # Extract tweet URL
                time_element = tweet.find_element(By.CSS_SELECTOR, 'time')
                tweet_url = time_element.find_element(By.XPATH, '..').get_attribute('href')
                
                # Check if this tweet is already in bookmarks
                if not any(b['url'] == tweet_url for b in bookmarks):
                    bookmarks.append({
                        "author": author,
                        "content": content,
                        "url": tweet_url
                    })
                    print(f"Scraped {len(bookmarks)} bookmarks", end='\r')
            except Exception as e:
                print(f"\nError extracting tweet data: {str(e)}")
        
        # Calculate new scroll height and compare with last scroll height
        new_height = driver.execute_script("return document.body.scrollHeight")
        if new_height == last_height:
            print("\nReached the end of bookmarks or no more new bookmarks to load.")
            break
        last_height = new_height
    
    print(f"\nFinished scraping. Total bookmarks scraped: {len(bookmarks)}")
    return bookmarks

def save_to_json(data, filename):
    script_dir = os.path.dirname(os.path.realpath(__file__))
    filepath = os.path.join(script_dir, filename)
    
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)
    
    print(f"Data saved to {filepath}")

def main():
    driver = webdriver.Chrome()  # Make sure you have ChromeDriver installed and in PATH
    
    try:
        if login_to_twitter(driver):
            bookmarks = scrape_bookmarks(driver)
            
            # Save bookmarks to JSON file
            save_to_json(bookmarks, 'twitter_bookmarks.json')
            
            print(f"Scraped {len(bookmarks)} bookmarks.")
        else:
            print("Login failed. Unable to scrape bookmarks.")
    
    finally:
        driver.quit()

if __name__ == "__main__":
    main()