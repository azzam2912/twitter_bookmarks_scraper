from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.keys import Keys
import time
import os
import signal
import twitter_scrape as scraper
import twitter_delete_bookmarks as deleter
import twitter_bookmark_adder as adder

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

if __name__ == "__main__":   
    driver = webdriver.Chrome()  # Make sure you have ChromeDriver installed and in PATH
    is_login = login_to_twitter(driver)
    while True:
        mode = input("What do you want to do? [scrape (1), delete (2), add bookmarks (3), exit (4)] (default scrape): ")
        try:
            if not mode or len(mode) == 0:
                mode = "1" 
            if mode == "1":
                scraper.main(driver, is_login, False, 0, set())
            elif mode == "2":
                deleter.main(driver, is_login, False, 0, set())
            elif mode == "3":
                adder.main(driver, is_login)  # Call the main function from the new module
            elif mode == "4":
                break
        except Exception as e:
            print(f"An error occurred. Please try again\n\n Error: {str(e)}")
            break

    driver.quit()

    