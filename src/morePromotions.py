import logging

from src.browser import Browser

from .activities import Activities


class MorePromotions:
    def __init__(self, browser: Browser):
        self.browser = browser
        self.activities = Activities(browser)

    def complete_more_promotions(self):
        # Function to complete More Promotions
        logging.info("[MORE PROMOS] " + "Trying to complete More Promotions...")
        self.browser.utils.go_home()
        more_promotions = self.browser.utils.get_dashboard_data()["morePromotions"]
        i = 0
        for promotion in more_promotions:
            try:
                i += 1
                if (
                    promotion["complete"] is False
                    and promotion["pointProgressMax"] != 0
                ):
                    # Open the activity for the promotion
                    self.activities.open_more_promotions_activity(i)
                    if promotion["promotionType"] == "urlreward":
                        # Complete search for URL reward
                        self.activities.complete_search()
                    elif (
                        promotion["promotionType"] == "quiz"
                        and promotion["pointProgress"] == 0
                    ):
                        self.complete_point_progress_quizzes(promotion)
                    else:
                        # Default to completing search
                        self.activities.complete_search()
            except Exception:  # pylint: disable=broad-except
                # Reset tabs in case of an exception
                self.browser.utils.reset_tabs()
        logging.info("[MORE PROMOS] Completed More Promotions successfully !")

    def complete_point_progress_quizzes(self, promotion):
        # Complete different types of quizzes based on point progress max
        if promotion["pointProgressMax"] == 10:
            self.activities.complete_abc()
        elif promotion["pointProgressMax"] in [30, 40]:
            self.activities.complete_quiz()
        elif promotion["pointProgressMax"] == 50:
            self.activities.complete_this_or_that()
