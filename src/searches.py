import json
import logging
import random
import time
from datetime import date, timedelta

import requests
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.by import By

from src.browser import Browser

MAX_RETRIES = 5

class Searches:
    def __init__(self, browser: Browser):
        self.browser = browser
        self.webdriver = browser.webdriver

    def getGoogleTrends(self, wordsCount: int) -> list:
        searchTerms: list[str] = []
        i = 0
        while len(searchTerms) < wordsCount:
            i += 1
            r = requests.get(
                f'https://trends.google.com/trends/api/dailytrends?hl={self.browser.localeLang}&ed={(date.today() - timedelta(days=i)).strftime("%Y%m%d")}&geo={self.browser.localeGeo}&ns=15'
            )
            trends = json.loads(r.text[6:])
            for topic in trends["default"]["trendingSearchesDays"][0][
                "trendingSearches"
            ]:
                searchTerms.append(topic["title"]["query"].lower())
                searchTerms.extend(
                    relatedTopic["query"].lower()
                    for relatedTopic in topic["relatedQueries"]
                )
            searchTerms = list(set(searchTerms))
        del searchTerms[wordsCount : (len(searchTerms) + 1)]
        return searchTerms

    def getRelatedTerms(self, word: str) -> list:
        try:
            r = requests.get(
                f"https://api.bing.com/osjson.aspx?query={word}",
                headers={"User-agent": self.browser.userAgent},
            )
            return r.json()[1]
        except Exception:  # pylint: disable=broad-except
            return []

    def bingSearches(self, numberOfSearches: int, pointsCounter: int = 0):
        logging.info(
            "[BING] "
            + f"Starting {self.browser.browserType.capitalize()} Edge Bing searches...",
        )

        i = 0
        search_terms = self.getGoogleTrends(numberOfSearches)
        for word in search_terms:
            i += 1
            logging.info("[BING] " + f"{i}/{numberOfSearches}")
            points = self.bingSearch(word)
            if points <= pointsCounter:
                relatedTerms = self.getRelatedTerms(word)[:2]
                for term in relatedTerms:
                    points = self.bingSearch(term)
                    if not points <= pointsCounter:
                        break
            if points > 0:
                pointsCounter = points
            else:
                break
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
        return self.browser.utils.getBingAccountPoints()