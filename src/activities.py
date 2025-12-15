import logging
import random
import time
from time import sleep

from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from src.browser import Browser


class Activities:
    def __init__(self, browser: Browser):
        self.browser = browser
        self.webdriver = browser.webdriver

    def open_hero_activity(self):
        try:
            self.webdriver.find_element(By.XPATH, "//mee-rewards-promotion").click()
            time.sleep(3)
            if self.browser.utils.wait_until_hero_banner_loads():
                wait = WebDriverWait(self.webdriver, 10)
                element = wait.until(
                    EC.element_to_be_clickable(
                        (
                            By.XPATH,
                            "/html/body/div[5]/div[2]/div[2]/mee-rewards-legal-text-box/div/div/div/div[3]/a",
                        )
                    )
                )
            self.webdriver.execute_script("arguments[0].click();", element)
            time.sleep(3)
            logging.info("[HERO] Hero promotion banner clicked")
        except Exception:
            logging.info("[HERO] No promotion to be clicked.")
        self.browser.utils.go_home()

    def open_daily_set_activity(self, card_id: int):
        self.webdriver.find_element(
            By.XPATH,
            f'//*[@id="daily-sets"]/mee-card-group[1]/div/mee-card[{card_id}]/div/card-content/mee-rewards-daily-set-item-content/div/a',
        ).click()
        self.browser.utils.switch_to_new_tab(8)

    def open_more_promotions_activity(self, card_id: int):
        element = self.webdriver.find_element(
            By.XPATH,
            f'//*[@id="more-activities"]/div/mee-card[{card_id}]/div/card-content/mee-rewards-more-activities-card-item/div/a',
        )
        logging.debug(f"[MORE PROMOS] {element.text}")
        element.click()
        self.browser.utils.switch_to_new_tab(8)

    def complete_search(self):
        time.sleep(random.randint(5, 10))
        self.browser.utils.close_current_tab()

    def complete_survey(self):
        self.webdriver.find_element(By.ID, f"btoption{random.randint(0, 1)}").click()
        time.sleep(random.randint(10, 15))
        self.browser.utils.close_current_tab()

    def complete_quiz(self):
        if not self.browser.utils.wait_until_quiz_loads():
            self.browser.utils.reset_tabs()
            return
        self.webdriver.find_element(By.XPATH, '//*[@id="rqStartQuiz"]').click()
        self.browser.utils.wait_until_visible(
            By.XPATH, '//*[@id="currentQuestionContainer"]/div/div[1]', 5
        )
        time.sleep(3)
        number_of_questions = self.webdriver.execute_script(
            "return _w.rewardsQuizRenderInfo.maxQuestions"
        )
        number_of_options = self.webdriver.execute_script(
            "return _w.rewardsQuizRenderInfo.numberOfOptions"
        )
        self.complete_questions(number_of_options, number_of_questions)
        time.sleep(5)
        self.browser.utils.close_current_tab()

    def complete_questions(self, number_of_options, number_of_questions):
        for question in range(number_of_questions):
            if number_of_options == 8:
                self.complete_eight_options_questions(number_of_options)
            elif number_of_options in [2, 3, 4]:
                self.complete_two_to_four_questions(number_of_options)
            if question + 1 != number_of_questions:
                time.sleep(5)

    def complete_two_to_four_questions(self, number_of_options):
        correct_option = self.webdriver.execute_script(
            "return _w.rewardsQuizRenderInfo.correctAnswer"
        )
        for i in range(number_of_options):
            if (
                self.webdriver.find_element(By.ID, f"rqAnswerOption{i}").get_attribute(
                    "data-option"
                )
                == correct_option
            ):
                self.webdriver.find_element(By.ID, f"rqAnswerOption{i}").click()
                time.sleep(5)
                if not self.browser.utils.wait_until_question_refresh():
                    self.browser.utils.reset_tabs()
                break

    def complete_eight_options_questions(self, number_of_options):
        answers = []
        for i in range(number_of_options):
            is_correct_option = self.webdriver.find_element(
                By.ID, f"rqAnswerOption{i}"
            ).get_attribute("iscorrectoption")
            if is_correct_option and is_correct_option.lower() == "true":
                answers.append(f"rqAnswerOption{i}")
        for answer in answers:
            self.webdriver.find_element(By.ID, answer).click()
            time.sleep(5)
            if not self.browser.utils.wait_until_question_refresh():
                self.browser.utils.reset_tabs()

    def complete_abc(self):
        counter = self.webdriver.find_element(
            By.XPATH, '//*[@id="QuestionPane0"]/div[2]'
        ).text[:-1][1:]
        number_of_questions = max(int(s) for s in counter.split() if s.isdigit())
        for question in range(number_of_questions):
            self.webdriver.find_element(
                By.ID, f"questionOptionChoice{question}{random.randint(0, 2)}"
            ).click()
            time.sleep(5)
            self.webdriver.find_element(By.ID, f"nextQuestionbtn{question}").click()
            time.sleep(3)
        time.sleep(5)
        self.browser.utils.close_current_tab()

    def complete_this_or_that(self):
        if not self.browser.utils.wait_until_quiz_loads():
            self.browser.utils.reset_tabs()
            return
        self.webdriver.find_element(By.XPATH, '//*[@id="rqStartQuiz"]').click()
        self.browser.utils.wait_until_visible(
            By.XPATH, '//*[@id="currentQuestionContainer"]/div/div[1]', 10
        )
        time.sleep(3)
        for _ in range(10):
            correct_answer_code = self.webdriver.execute_script(
                "return _w.rewardsQuizRenderInfo.correctAnswer"
            )
            answer1, answer1_code = self.get_answer_and_code("rqAnswerOption0")
            answer2, answer2_code = self.get_answer_and_code("rqAnswerOption1")
            if answer1_code == correct_answer_code:
                answer1.click()
                time.sleep(8)
            elif answer2_code == correct_answer_code:
                answer2.click()
                time.sleep(8)

        time.sleep(5)
        self.browser.utils.close_current_tab()

    def get_answer_and_code(self, answer_id: str) -> tuple:
        answer_encode_key = self.webdriver.execute_script("return _G.IG")
        answer = self.webdriver.find_element(By.ID, answer_id)
        answer_title = answer.get_attribute("data-option")
        if answer_title is not None:
            return (
                answer,
                self.browser.utils.get_answer_code(answer_encode_key, answer_title),
            )
        else:
            return (answer, None)
