import json
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, StaleElementReferenceException, NoSuchElementException
from twitter_scrape import *

URL = "https://twitter.com/i/bookmarks"

def delete_bookmarks(driver, max_deletions=1000, scroll_pause_time=1.2, is_continue=False, scroll_position=0, processed_urls=set(), delete_all=False, json_file=None):
    existing_urls = set()
    if not delete_all and json_file:
        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                existing_bookmarks = json.load(f)
            existing_urls = set(bookmark['url'] for bookmark in existing_bookmarks)
        except FileNotFoundError:
            print(f"JSON file {json_file} not found. Proceeding to delete all bookmarks.")
            delete_all = True

    deleted_count = 0

    if not is_continue:
        driver.get(URL)
        time.sleep(scroll_pause_time + 2)

    first_tweet = WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, 'article[data-testid="tweet"]'))
    )
    tweet_height = first_tweet.size['height']

    counter = 0
    scroll_position_old = scroll_position
    while deleted_count < max_deletions:
        try:
            driver.execute_script(f"window.scrollTo(0, {scroll_position});")
            time.sleep(scroll_pause_time)

            tweets = WebDriverWait(driver, 10).until(
                EC.presence_of_all_elements_located((By.CSS_SELECTOR, 'article[data-testid="tweet"]'))
            )

            for tweet in tweets:
                if deleted_count >= max_deletions:
                    break

                try:
                    tweet_height = tweet.size['height']
                    time_element = tweet.find_element(By.CSS_SELECTOR, 'time')
                    tweet_url = time_element.find_element(By.XPATH, '..').get_attribute('href')

                    if tweet_url in processed_urls:
                        continue

                    if delete_all or tweet_url in existing_urls:
                        bookmark_button = tweet.find_element(By.CSS_SELECTOR, 'button[data-testid="removeBookmark"]')
                        bookmark_button.click()
                        deleted_count += 1
                        print(f"Deleted bookmark: {tweet_url}")

                    processed_urls.add(tweet_url)
                    scroll_position += tweet_height
                    print(f"Processed {len(processed_urls)} tweets, Deleted {deleted_count} bookmarks", end='\r')

                except (StaleElementReferenceException, NoSuchElementException):
                    print("\nElement exception occurred. Continuing to the next tweet...")
                    continue
                except TimeoutException:
                    print("\nNo more tweets loaded. Reached the end of bookmarks.")
                    break
                except KeyboardInterrupt:
                    print("\nKeyboard interrupt. Ending deletion process.")
                    return scroll_position, processed_urls
                except Exception as e:
                    print(f"\nError processing tweet: {str(e)}")

            if scroll_position == scroll_position_old:
                counter += 1
                print("No new tweets loaded. Counter:", counter)
                if counter > 5:
                    print("\nReached the end of bookmarks.")
                    break
                time.sleep(3)
            else:
                counter = 0
            scroll_position_old = scroll_position

        except KeyboardInterrupt:
            print("\nKeyboard interrupt. Ending deletion process.")
            break
        except TimeoutException:
            print("\nNo more tweets loaded. Reached the end of bookmarks.")
            break

    print(f"\nFinished deleting. Total bookmarks deleted: {deleted_count}")
    return scroll_position, processed_urls

def main(driver, is_login, is_continue=False, scroll_position=0, processed_urls_set=set()):
    max_posts = input("Enter the maximum number of bookmarks to delete (default 1000): ") or "1000"
    max_posts = int(max_posts)
    scroll_pause_time = input("Enter the scroll pause time in seconds (default 1.2): ") or "1.2"
    scroll_pause_time = float(scroll_pause_time)
    
    delete_all = input("Do you want to delete all bookmarks without checking a JSON file? (y/n, default n): ").lower() == 'y'
    
    json_file = None
    if not delete_all:
        json_file = input("Enter the JSON file name (default twitter_bookmarks.json): ") or "twitter_bookmarks.json"

    try:
        if is_login:
            scroll_position, processed_urls_set = delete_bookmarks(
                driver, max_posts, scroll_pause_time, is_continue, scroll_position, 
                processed_urls_set, delete_all, json_file
            )
        else:
            print("Login failed. Unable to delete bookmarks.")
    except Exception as e:
        print(f"An error occurred: {str(e)}")
    finally:
        while True:
            finish_prompt = input("Do you want to continue deleting? (y/n) ")
            if finish_prompt.lower() == "n":
                break
            elif finish_prompt.lower() == "y":
                main(driver, is_login, True, scroll_position, processed_urls_set)
                break