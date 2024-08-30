import logging
import urllib.parse
from datetime import datetime

from src.browser import Browser

from .activities import Activities


class DailySet:
    def __init__(self, browser: Browser):
        self.browser = browser
        self.webdriver = browser.webdriver
        self.activities = Activities(browser)

    def complete_daily_set(self):
        # Function to complete the Daily Set
        logging.info("[DAILY SET] " + "Trying to complete the Daily Set...")
        self.browser.utils.go_home()
        data = self.browser.utils.get_dashboard_data()["dailySetPromotions"]
        today_date = datetime.now().strftime("%m/%d/%Y")
        for activity in data.get(today_date, []):
            try:
                if activity["complete"] is False:
                    card_id = int(activity["offerId"][-1:])
                    # Open the Daily Set activity
                    self.activities.open_daily_set_activity(card_id)
                    self.complete_url_reward_promotion(activity, card_id)
                    if activity["promotionType"] == "quiz":
                        if (
                            activity["pointProgressMax"] == 50
                            and activity["pointProgress"] == 0
                        ):
                            logging.info(
                                "[DAILY SET] "
                                + f"Completing This or That of card {card_id}"
                            )
                            # Complete This or That for a specific point progress max
                            self.activities.complete_this_or_that()
                        elif (
                            activity["pointProgressMax"] in [40, 30]
                            and activity["pointProgress"] == 0
                        ):
                            logging.info(
                                f"[DAILY SET] Completing quiz of card {card_id}"
                            )
                            # Complete quiz for specific point progress max
                            self.activities.complete_quiz()
                        elif (
                            activity["pointProgressMax"] == 10
                            and activity["pointProgress"] == 0
                        ):
                            # Extract and parse search URL for additional checks
                            search_url = urllib.parse.unquote(
                                urllib.parse.parse_qs(
                                    urllib.parse.urlparse(
                                        activity["destinationUrl"]
                                    ).query
                                )["ru"][0]
                            )
                            search_url_queries = urllib.parse.parse_qs(
                                urllib.parse.urlparse(search_url).query
                            )
                            filters = {}
                            for filter_el in search_url_queries["filters"][0].split(" "):
                                filter_el = filter_el.split(":", 1)
                                filters[filter_el[0]] = filter_el[1]
                            if "PollScenarioId" in filters:
                                logging.info(
                                    f"[DAILY SET] Completing poll of card {card_id}"
                                )
                                # Complete survey for a specific scenario
                                self.activities.complete_survey()
                            else:
                                logging.info(
                                    f"[DAILY SET] Completing quiz of card {card_id}"
                                )
                                try:
                                    # Try completing ABC activity
                                    self.activities.complete_abc()
                                except Exception:  # pylint: disable=broad-except
                                    # Default to completing quiz
                                    self.activities.complete_quiz()
            except Exception:  # pylint: disable=broad-except
                # Reset tabs in case of an exception
                self.browser.utils.reset_tabs()
        logging.info("[DAILY SET] Completed the Daily Set successfully !")

    def complete_url_reward_promotion(self, activity, card_id):
        if activity["promotionType"] == "urlreward":
            logging.info(f"[DAILY SET] Completing search of card {card_id}")
            # Complete search for URL reward
            self.activities.complete_search()
