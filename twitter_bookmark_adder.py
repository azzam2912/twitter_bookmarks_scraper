import json
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException, TimeoutException, StaleElementReferenceException
from selenium.webdriver.common.keys import Keys
import time
import os
import glob

def load_previously_added_bookmarks():
    previously_added = set()
    script_dir = os.path.dirname(os.path.realpath(__file__))
    bookmark_dir = os.path.join(script_dir, "bookmarks")
    for filename in glob.glob(os.path.join(bookmark_dir, 'added_bookmarks_*.json')):
        with open(filename, 'r', encoding='utf-8') as f:
            bookmarks = json.load(f)
            previously_added.update(bookmark['url'] for bookmark in bookmarks)
    return previously_added

def add_bookmarks(driver, bookmarks_data, max_bookmarks=1000, pause_time=1.2, is_continue=False, start_index=0):
    bookmarks_added = []
    previously_added = load_previously_added_bookmarks()
    
    for i, bookmark in enumerate(bookmarks_data[start_index:max_bookmarks], start=start_index):
        url = bookmark['url']
        
        if url in previously_added:
            print(f"Skipping already bookmarked: {url}")
            continue
        
        try:
            # Navigate to the tweet
            driver.get(url)
            time.sleep(pause_time)
            
            # Wait for the tweet to load
            tweet = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, 'article[data-testid="tweet"]'))
            )
            
            # Find the bookmark and like button
            bookmark_button = tweet.find_element(By.CSS_SELECTOR, 'button[data-testid="bookmark"]')
            like_button = tweet.find_element(By.CSS_SELECTOR, 'button[data-testid="like"]')
            # Click the bookmark button
            bookmark_button.click()
            like_button.click()
            time.sleep(pause_time)
            
            bookmarks_added.append(bookmark)
            previously_added.add(url)
            
            print(f"Bookmarked: {url}")
            print(f"Bookmarks added: {len(bookmarks_added)}", end='\r')
            
        except StaleElementReferenceException:
            print(f"\nStale element reference for URL: {url}. Skipping...")
            continue
        except TimeoutException:
            print(f"\nTimeout occurred while processing URL: {url}. Skipping...")
            continue
        except KeyboardInterrupt:
            print("\nKeyboard interrupt. Stopping bookmark addition.")
            break
        except Exception as e:
            print(f"\nError processing URL {url}: {str(e)}")
    
    print(f"\nFinished adding bookmarks. Total bookmarks added: {len(bookmarks_added)}")
    return bookmarks_added, i + 1

def save_to_json(data, filename):
    script_dir = os.path.dirname(os.path.realpath(__file__))
    filepath = os.path.join(script_dir, "bookmarks")
    filepath = os.path.join(filepath, filename)
    
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)
    
    print(f"Data saved to {filepath}")

def main(driver, is_login, is_continue=False, start_index=0):
    if not is_login:
        print("Login failed. Unable to add bookmarks.")
        return

    if not is_continue:
        max_bookmarks = input("Enter the maximum number of bookmarks to add (default 1000): ")
        max_bookmarks = int(max_bookmarks) if max_bookmarks else 1000

        pause_time = input("Enter the pause time between actions in seconds (default 1.2): ")
        pause_time = float(pause_time) if pause_time else 1.2

        json_file = input("Enter the name of the JSON file containing bookmarks data (default bookmarks.json): ")
        json_file = json_file if json_file else "bookmarks.json"

        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                bookmarks_data = json.load(f)
        except FileNotFoundError:
            print(f"File {json_file} not found. Please make sure the file exists.")
            return
        except json.JSONDecodeError:
            print(f"Error decoding JSON from {json_file}. Please ensure it's a valid JSON file.")
            return
    else:
        # If continuing, use the existing values (you may want to store these in a config file or pass them as arguments)
        max_bookmarks = 1000  # or load from config
        pause_time = 1.2  # or load from config
        json_file = "bookmarks.json"  # or load from config
        with open(json_file, 'r', encoding='utf-8') as f:
            bookmarks_data = json.load(f)

    try:
        bookmarks_added, next_start_index = add_bookmarks(driver, bookmarks_data, max_bookmarks, pause_time, is_continue, start_index)
        current_time = time.strftime("%Y_%m_%d_%H_%M_%S")
        save_to_json(bookmarks_added, f'added_bookmarks_{current_time}.json')
    except Exception as e:
        print(f"An error occurred: {str(e)}")
    finally:
        # Prompt to continue adding bookmarks
        while True:
            finish_prompt = input("Do you want to continue adding bookmarks? (y/n) ")
            if finish_prompt.lower() == "n":
                break
            elif finish_prompt.lower() == "y":
                main(driver, is_login, True, next_start_index)
                break
            else:
                continue