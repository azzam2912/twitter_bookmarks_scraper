from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException, TimeoutException, StaleElementReferenceException
from selenium.webdriver.common.keys import Keys
from datetime import datetime
import time
import json
import os
import signal

def timeout():
    def handler():
        print("Timed out! Have waiting for 10 seconds. Maybe it has done or try again later.")
        raise TimeoutException
    signal.signal(signal.SIGALRM, handler)
    signal.alarm(10)

def login_to_twitter(driver):
    username = os.environ.get("USERNAME")
    number = os.environ.get("NUMBER")
    password = os.environ.get("PASSWORD")
    driver.get("https://twitter.com/i/flow/login")
    
    try:
        # Wait for and enter username
        username_field = WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, 'input[autocomplete="username"][name="text"]'))
        )
        username_field.send_keys(username)
        time.sleep(1)  # Short pause
        
        # Find and click the "Next" button
        next_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, '//div[@role="button"]//span[text()="Next"]'))
        )
        next_button.click()
        time.sleep(2)  # Wait for the next page to load
        
        # Wait for and enter password
        password_field = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, 'input[name="password"]'))
        )
        password_field.send_keys(password)
        time.sleep(1)  # Short pause
        
        # Find and click the "Log in" button
        login_button = WebDriverWait(driver, 10).until(
            EC.element_to_be_clickable((By.XPATH, '//div[@role="button"]//span[text()="Log in"]'))
        )
        login_button.click()
        
        # Wait for the home page to load
        WebDriverWait(driver, 20).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, 'div[data-testid="primaryColumn"]'))
        )
        print("Login successful")
        return True
    
    except Exception as e:
        print("Please log in manually in the browser window.")
        print("After logging in, navigate to your Twitter homepage.")
        input("Press Enter when you've successfully logged in and are on the Twitter homepage...")
        return True

def scrape_bookmarks(driver, max_posts=1000, scroll_pause_time=1.2, is_continue=False, scroll_position=0, processed_urls=set()):
    bookmarks = []
    
    if not is_continue:
        driver.get("https://twitter.com/i/bookmarks")
        time.sleep(scroll_pause_time+2)
        # Wait for the first tweet to load to get its height
    first_tweet = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, 'article[data-testid="tweet"]'))
    )
    tweet_height = first_tweet.size['height']

    counter = 0
    scroll_position_old = scroll_position
    while len(bookmarks) < max_posts:
        try:
            # Scroll to the next position
            driver.execute_script(f"window.scrollTo(0, {scroll_position});")
            time.sleep(scroll_pause_time)
            # Wait for tweets to load
            tweets = WebDriverWait(driver, 10).until(
                EC.presence_of_all_elements_located((By.CSS_SELECTOR, 'article[data-testid="tweet"]'))
            )
            
            for tweet in tweets:
                if len(bookmarks) >= max_posts:
                    break
                
                try:
                    tweet_height = tweet.size['height']
                    # Extract tweet URL
                    time_element = tweet.find_element(By.CSS_SELECTOR, 'time')
                    tweet_url = time_element.find_element(By.XPATH, '..').get_attribute('href')
                    
                    # If we've already processed this tweet, skip it
                    if tweet_url in processed_urls:
                        continue
                    
                    # Extract tweet data
                    author = tweet.find_element(By.CSS_SELECTOR, 'div[data-testid="User-Name"]').text
                    try:
                        content = tweet.find_element(By.CSS_SELECTOR, 'div[data-testid="tweetText"]').text
                    except NoSuchElementException:
                        content = "[No text content]"

                    # Extract image URLs
                    image_urls = []
                    try:
                        images = tweet.find_elements(By.CSS_SELECTOR, 'img[alt="Image"]')
                        for img in images:
                            image_url = img.get_attribute('src')
                            if image_url:
                                image_urls.append(image_url)
                    except NoSuchElementException:
                        pass
                    
                    # Extract video URLs
                    video_urls = []
                    try:
                        # First, look for the video component
                        video_components = tweet.find_elements(By.CSS_SELECTOR, 'div[data-testid="videoComponent"]')
                        for component in video_components:
                            # Find the video element within the component
                            video_element = component.find_element(By.TAG_NAME, 'video')
                            
                            # Try to get the poster (thumbnail) URL
                            video_url = video_element.get_attribute('poster')
                            if video_url and "pbs.twimg.com" in video_url or "twimg" in video_url:
                                image_urls.append(video_url)
                            elif video_url:
                                video_urls.append(video_url)
                            
                            # Try to get the source element and its src attribute
                            try:
                                source_element = video_element.find_element(By.TAG_NAME, 'source')
                                video_url = source_element.get_attribute('src')
                                if video_url and "pbs.twimg.com" in video_url or "twimg" in video_url:
                                    image_urls.append(video_url)
                                elif video_url:
                                    video_urls.append(video_url)
                            except NoSuchElementException:
                                # If there's no source element, we'll use the tweet URL with a video indicator
                                video_urls.append(f"{tweet_url}#video")
                    except NoSuchElementException:
                        pass

                    bookmarks.append({
                        "author": author,
                        "content": content,
                        "url": tweet_url,
                        "image_urls": image_urls,
                        "video_urls": video_urls
                    })
                    processed_urls.add(tweet_url)
                    # Increment scroll position by one tweet height
                    scroll_position += tweet_height
                    print(f"Scraped {len(bookmarks)} bookmarks", end='\r')
                
                except StaleElementReferenceException:
                    # If the element becomes stale, continue to the next tweet
                    print("\nStale element reference exception occurred. Continuing to the next tweet...")
                    continue
                except TimeoutException:
                    print("\nNo more tweets loaded [>>11111<<]. Reached the end of bookmarks.")
                    break
                except KeyboardInterrupt:
                    print("\nKeyboard interrupt [>>11111<<]. Reached the end of scraping.")
                    print(f"\nFinished scraping. Total bookmarks scraped: {len(bookmarks)}")
                    return bookmarks, scroll_position, processed_urls
                except Exception as e:
                    print(f"\nError extracting tweet data: {str(e)}")

            # Check if we've reached the end of the page
            if scroll_position == scroll_position_old:
                counter += 1
                print("counter become (max 5)", counter)
                if counter > 5:
                    print("\nNo more tweets loaded. Reached the end of bookmarks.")
                    break
                time.sleep(3)
                print("waited 3 seconds")
            else:
                counter = 0
            scroll_position_old = scroll_position
                
        except KeyboardInterrupt:
            print("\nKeyboard interrupt [>>22222<<]. Reached the end of scraping.")
            print(f"\nFinished scraping. Total bookmarks scraped: {len(bookmarks)}")
            return bookmarks, scroll_position, processed_urls
        except TimeoutException:
            print("\nNo more tweets loaded [>>22222<<]. Reached the end of bookmarks.")
            break

    print(f"\nFinished scraping. Total bookmarks scraped: {len(bookmarks)}")
    return bookmarks, scroll_position, processed_urls

def save_to_json(data, filename):
    script_dir = os.path.dirname(os.path.realpath(__file__))
    filepath = os.path.join(script_dir, filename)
    
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)
    
    print(f"Data saved to {filepath}")

def main(driver, is_login, is_continue=False, scroll_position=0, processed_urls_set = set()):
    max_posts = input("Enter the maximum number of bookmarks to scrape (by default 1000): ")
    if not max_posts or len(max_posts) == 0:
        max_posts = 1000
    max_posts = int(max_posts)
    scroll_pause_time = input("Enter the scroll pause time in seconds (by default 1.2): ")
    if not scroll_pause_time or len(scroll_pause_time) == 0:
        scroll_pause_time = 1.2
    scroll_pause_time = float(scroll_pause_time)
    try:
        if is_login:
            # Scrape bookmarks
            bookmarks, scroll_position, processed_urls_set = scrape_bookmarks(driver, max_posts, scroll_pause_time, is_continue, scroll_position, processed_urls_set)
            # Save bookmarks to JSON file
            current_time = datetime.now().strftime("%Y_%m_%d_%H_%M_%S")
            save_to_json(bookmarks, f'twitter_bookmarks___{current_time}___{len(bookmarks)}.json')
            print(f"Scraped {len(bookmarks)} bookmarks.")
        else:
            print("Login failed. Unable to scrape bookmarks.")
    except Exception as e:
        print(f"An error occurred: {str(e)}")
    finally:
        # Close the driver if the standard input say yes
        while True:
            finish_prompt = input("Do you want to continue scraping? (y/n) ")
            if finish_prompt == "n":
                driver.quit()
                break
            elif finish_prompt == "y":
                main(driver, is_login, True, scroll_position, processed_urls_set)
                break
            else:
                continue

if __name__ == "__main__":
    driver = webdriver.Chrome()  # Make sure you have ChromeDriver installed and in PATH
    is_login = login_to_twitter(driver)
    main(driver, is_login, False, 0, set())