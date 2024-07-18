import logging
import random
import time
from faker import Faker

from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.by import By

from src.browser import Browser

MAX_RETRIES = 3
fake = Faker()

class Searches:
    def __init__(self, browser: Browser):
        self.browser = browser
        self.webdriver = browser.webdriver

    def getNewSearchTerm (self) -> str:
        return fake.name()

    def bingSearches(self, numberOfSearches: int, pointsCounter: int = 0):
        logging.info(
            "[BING] "
            + f"Starting {self.browser.browserType.capitalize()} Edge Bing searches...",
        )

        for i in range(1, numberOfSearches + 1):
            searchTerm = self.getNewSearchTerm()
            logging.info(f"[BING] [{i}/{numberOfSearches}] \t '{searchTerm}'")
            self.bingSearch(searchTerm)
        logging.info(
            f"[BING] Finished {self.browser.browserType.capitalize()} Edge Bing searches !"
        )
        return pointsCounter

    def bingSearch(self, word: str):
        numOfRetries = 0
        while True:
            try:
                self.webdriver.get("https://bing.com")
                self.browser.utils.waitUntilClickable(By.ID, "sb_form_q")
                searchbar = self.webdriver.find_element(By.ID, "sb_form_q")
                searchbar.send_keys(word)
                searchbar.submit()
                time.sleep(random.randint(self.browser.sleep - 10, self.browser.sleep + 10))
                return self.browser.utils.getBingAccountPoints()
            except TimeoutException:
                if numOfRetries == MAX_RETRIES:
                    break
                else:
                    numOfRetries += 1
                    logging.error(f"[BING] Timeout {numOfRetries}/{MAX_RETRIES}, retrying in 5 seconds...")
                    time.sleep(5)
                    continue