import json
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, StaleElementReferenceException
from twitter_scrape import *

URL = "https://twitter.com/i/bookmarks"
def delete_existing_bookmarks(driver, json_file, max_deletions=1000, scroll_pause_time=1.2, is_continue=False, scroll_position=0, processed_urls=set()):
    # Load existing bookmarks from JSON file
    try:
        with open(json_file, 'r', encoding='utf-8') as f:
            existing_bookmarks = json.load(f)
    except FileNotFoundError:
        print(f"JSON file {json_file} not found. No bookmarks will be deleted.")
        return

    existing_urls = set(bookmark['url'] for bookmark in existing_bookmarks)
    deleted_count = 0

    if not is_continue:
        driver.get(URL)
        time.sleep(scroll_pause_time + 2)

    # Wait for the first tweet to load to get its height
    first_tweet = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, 'article[data-testid="tweet"]'))
    )
    tweet_height = first_tweet.size['height']

    counter = 0
    scroll_position_old = scroll_position
    while deleted_count < max_deletions:
        try:
            # Scroll to the next position
            driver.execute_script(f"window.scrollTo(0, {scroll_position});")
            time.sleep(scroll_pause_time)

            # Wait for tweets to load
            tweets = WebDriverWait(driver, 10).until(
                EC.presence_of_all_elements_located((By.CSS_SELECTOR, 'article[data-testid="tweet"]'))
            )

            for tweet in tweets:
                if deleted_count >= max_deletions:
                    break

                try:
                    tweet_height = tweet.size['height']
                    # Extract tweet URL
                    time_element = tweet.find_element(By.CSS_SELECTOR, 'time')
                    tweet_url = time_element.find_element(By.XPATH, '..').get_attribute('href')

                    # If we've already processed this tweet, skip it
                    if tweet_url in processed_urls:
                        continue

                    if tweet_url in existing_urls:
                        # Click the bookmark button to remove the bookmark
                        bookmark_button = tweet.find_element(By.CSS_SELECTOR, 'button[data-testid="removeBookmark"]')
                        bookmark_button.click()
                        deleted_count += 1
                        print(f"Deleted bookmark: {tweet_url}")

                    processed_urls.add(tweet_url)
                    # Increment scroll position by one tweet height
                    scroll_position += tweet_height
                    print(f"Processed {len(processed_urls)} tweets, Deleted {deleted_count} bookmarks", end='\r')

                except StaleElementReferenceException:
                    print("\nStale element reference exception occurred. Continuing to the next tweet...")
                    continue
                except NoSuchElementException:
                    print("\nNo such element exception occurred. Continuing to the next tweet...")
                    continue
                except TimeoutException:
                    print("\nNo more tweets loaded [>>11111<<]. Reached the end of bookmarks.")
                    break
                except KeyboardInterrupt:
                    print("\nKeyboard interrupt [>>11111<<]. Reached the end of deletion.")
                    print(f"\nFinished deleting. Total bookmarks deleted: {deleted_count}")
                    return scroll_position, processed_urls
                except Exception as e:
                    print(f"\nError processing tweet: {str(e)}")

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
            print("\nKeyboard interrupt [>>22222<<]. Reached the end of deletion.")
            print(f"\nFinished deleting. Total bookmarks deleted: {deleted_count}")
            return scroll_position, processed_urls
        except TimeoutException:
            print("\nNo more tweets loaded [>>22222<<]. Reached the end of bookmarks.")
            break

    print(f"\nFinished deleting. Total bookmarks deleted: {deleted_count}")
    return scroll_position, processed_urls

def main(driver, is_login, is_continue=False, scroll_position=0, processed_urls_set = set()):
    max_posts = input("Enter the maximum number of bookmarks to delete (by default 1000): ")
    if not max_posts or len(max_posts) == 0:
        max_posts = 1000
    max_posts = int(max_posts)
    scroll_pause_time = input("Enter the scroll pause time in seconds (by default 1.2): ")
    if not scroll_pause_time or len(scroll_pause_time) == 0:
        scroll_pause_time = 1.2
    scroll_pause_time = float(scroll_pause_time)
    json_file = input("Enter the JSON file name (by default twitter_bookmarks.json): ")
    if not json_file or len(json_file) == 0:
        json_file = "twitter_bookmarks.json"
    try:
        if is_login:
            scroll_position, processed_urls_set = delete_existing_bookmarks(driver, json_file, max_posts, scroll_pause_time, is_continue, scroll_position, processed_urls_set)
        else:
            print("Login failed. Unable to delete bookmarks.")
    except Exception as e:
        print(f"An error occurred: {str(e)}")
    finally:
        # Close the driver if the standard input say yes
        while True:
            finish_prompt = input("Do you want to continue deleting? (y/n) ")
            if finish_prompt == "n":
                break
            elif finish_prompt == "y":
                main(driver, is_login, True, scroll_position, processed_urls_set)
                break
            else:
                continue
    