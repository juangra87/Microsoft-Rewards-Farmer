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

    def get_new_search_term (self) -> str:
        return fake.name()

    def bing_searches(self, number_of_searches: int, points_counter: int = 0):
        logging.info(
            "[BING] "
            + f"Starting {self.browser.browser_type.capitalize()} Edge Bing searches...",
        )

        for i in range(1, number_of_searches + 1):
            search_term = self.get_new_search_term()
            logging.info(f"[BING] [{i}/{number_of_searches}] \t '{search_term}'")
            points_counter = self.bing_search(search_term)
        logging.info(
            f"[BING] Finished {self.browser.browser_type.capitalize()} Edge Bing searches !"
        )
        return points_counter

    def bing_search(self, word: str):
        num_of_retries = 0
        while True:
            try:
                self.webdriver.get("https://www.bing.com/search?q="+word+"&form=ASDSBP")
                # self.browser.utils.wait_until_clickable(By.ID, "sb_form_q")
                # searchbar = self.webdriver.find_element(By.ID, "sb_form_q")
                # searchbar.send_keys(word)
                # searchbar.submit()
                time.sleep(random.randint(self.browser.sleep - 10, self.browser.sleep + 10))
                return self.browser.utils.get_bing_account_points()
            except TimeoutException:
                if num_of_retries == MAX_RETRIES:
                    break
                else:
                    num_of_retries += 1
                    logging.error(f"[BING] Timeout {num_of_retries}/{MAX_RETRIES}, retrying in 5 seconds...")
                    time.sleep(5)
                    continue
