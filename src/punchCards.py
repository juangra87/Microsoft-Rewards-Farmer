import contextlib
import logging
import random
import time
import urllib.parse

from selenium.webdriver.common.by import By

from src.browser import Browser

from .constants import BASE_URL


class PunchCards:
    def __init__(self, browser: Browser):
        self.browser = browser
        self.webdriver = browser.webdriver

    def complete_punch_card(self, url: str, child_promotions: dict):
        self.webdriver.get(url)
        for child in child_promotions:
            if child["complete"] is False:
                if child["promotionType"] == "urlreward":
                    self.webdriver.find_element(By.CLASS_NAME, "offer-cta").click()
                    self.browser.utils.visit_new_tab(random.randint(13, 17))
                if child["promotionType"] == "quiz":
                    self.webdriver.find_element(By.CLASS_NAME, "offer-cta").click()
                    self.browser.utils.switch_to_new_tab(8)
                    counter = str(
                        self.webdriver.find_element(
                            By.XPATH, '//*[@id="QuestionPane0"]/div[2]'
                        ).get_attribute("innerHTML")
                    )[:-1][1:]
                    number_of_questions = max(
                        int(s) for s in counter.split() if s.isdigit()
                    )
                    for question in range(number_of_questions):
                        self.webdriver.find_element(
                            By.XPATH,
                            f'//*[@id="QuestionPane{question}"]/div[1]/div[2]/a[{random.randint(1, 3)}]/div',
                        ).click()
                        time.sleep(5)
                        self.webdriver.find_element(
                            By.XPATH,
                            f'//*[@id="AnswerPane{question}"]/div[1]/div[2]/div[4]/a/div/span/input',
                        ).click()
                        time.sleep(3)
                    time.sleep(5)
                    self.browser.utils.close_current_tab()

    def complete_punch_cards(self):
        logging.info("[PUNCH CARDS] " + "Trying to complete the Punch Cards...")
        self.complete_promotional_items()
        punch_cards = self.browser.utils.get_dashboard_data()["punchCards"]
        for punch_card in punch_cards:
            try:
                if (
                    punch_card["parentPromotion"]
                    and punch_card["childPromotions"]
                    and not punch_card["parentPromotion"]["complete"]
                    and punch_card["parentPromotion"]["pointProgressMax"] != 0
                ):
                    self.complete_punch_card(
                        punch_card["parentPromotion"]["attributes"]["destination"],
                        punch_card["childPromotions"],
                    )
            except Exception:  # pylint: disable=broad-except
                self.browser.utils.reset_tabs()
        logging.info("[PUNCH CARDS] Completed the Punch Cards successfully !")
        time.sleep(2)
        self.webdriver.get(BASE_URL)
        time.sleep(2)

    def complete_promotional_items(self):
        with contextlib.suppress(Exception):
            item = self.browser.utils.get_dashboard_data()["promotionalItem"]
            dest_url = urllib.parse.urlparse(item["destinationUrl"])
            base_url = urllib.parse.urlparse(BASE_URL)
            if (
                (item["pointProgressMax"] in [100, 200, 500])
                and not item["complete"]
                and (
                    (
                        dest_url.hostname == base_url.hostname
                        and dest_url.path == base_url.path
                    )
                    or dest_url.hostname == "www.bing.com"
                )
            ):
                self.webdriver.find_element(
                    By.XPATH, '//*[@id="promo-item"]/section/div/div/div/span'
                ).click()
                self.browser.utils.visit_new_tab(8)
