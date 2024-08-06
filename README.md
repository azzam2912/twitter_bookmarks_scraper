# Twitter Bookmarks Scraper
Provide the scraper agent by Selenium and the notebook for processing (classifying) the data into many categories.

- Make sure you already installed Python version ```>=3.12```
- Recommended to use virtual environment:

- Install Selenium

    ```pip install selenium```

- Install Chrome WebDriver

    For macOs ```brew install chromedriver```

- Now you are good to go :)

## To Scrape
To scrape you have to run ```twitter_bookmark_scraper.py```

please look at the terminal/command prompt to see the indicator or instruction.

You don't need to hardcoded your Twitter/X username and password.

Just change the max scraped post in the code (if needed).

## After Scrape
After scraping, you'll get json data that contains scraped post which consisted of author, content, and url.

Use the notebook (.ipynb) to classify the data into many categories. I used classical "machine learning" which is only lines of if-else, hehe.

The notebook is up to you to use, please use it wisely :).

## License: MIT
