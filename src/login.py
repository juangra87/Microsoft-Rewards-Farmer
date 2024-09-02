import contextlib
import logging
import time
import urllib.parse

from selenium.webdriver.common.by import By

from src.browser import Browser

logger_prefix = '[LOGIN] '


class Login:
    def __init__(self, browser: Browser):
        self.browser = browser
        self.webdriver = browser.webdriver
        self.utils = browser.utils

    def login(self):
        logging.info(logger_prefix + "Logging-in...")
        self.webdriver.get( "https://rewards.bing.com/Signin/")
        already_logged_in = False

        if not already_logged_in:
            self.execute_login()
        self.utils.try_dismiss_cookie_banner()

        logging.info(logger_prefix + "Logged-in !")

        self.utils.go_home()
        points = self.utils.get_account_points()

        logging.info(logger_prefix + "Ensuring login on Bing...")
        self.check_bing_login()

        logging.info("[LOGIN] Logged-in successfully !")
        return points

    def execute_login(self):
        logging.info(logger_prefix + "Entering email...")
        self.utils.wait_until_clickable(By.NAME, "loginfmt", 10)
        email_field = self.webdriver.find_element(By.NAME, "loginfmt")

        while True:
            email_field.send_keys(self.browser.username)
            time.sleep(3)
            if email_field.get_attribute("value") == self.browser.username:
                self.webdriver.find_element(By.ID, "idSIButton9").click()
                break

            email_field.clear()
            time.sleep(3)
        try:
            self.enter_password(self.browser.password)
        except Exception:  # pylint: disable=broad-except
            logging.error(logger_prefix + "2FA required !")
            with contextlib.suppress(Exception):
                code = self.webdriver.find_element(
                    By.ID, "idRemoteNGC_DisplaySign"
                ).get_attribute("innerHTML")
                logging.error(logger_prefix + f"2FA code: {code}")
            logging.info("[LOGIN] Press enter when confirmed...")
            input()

        self.utils.try_dismiss_all_messages()
        time.sleep(1)

    def enter_password(self, password):
        self.utils.wait_until_clickable(By.NAME, "passwd", 10)
        self.utils.wait_until_clickable(By.ID, "idSIButton9", 10)
        password = password.replace("\\", "\\\\").replace('"', '\\"')
        self.webdriver.find_element(By.NAME, "passwd").send_keys(password)
        logging.info("[LOGIN] " + "Writing password...")
        time.sleep(3)
        self.webdriver.find_element(By.ID, "idSIButton9").click()

    def check_bing_login(self):
        self.webdriver.get(
            "https://www.bing.com/fd/auth/signin?action=interactive&provider=windows_live_id&return_url=https%3A%2F%2Fwww.bing.com%2F"
        )
        for _ in range(5):
            current_url = urllib.parse.urlparse(self.webdriver.current_url)
            if current_url.hostname == "www.bing.com" and current_url.path == "/":
                time.sleep(3)
                self.utils.try_dismiss_bing_cookie_banner()
                with contextlib.suppress(Exception):
                    if self.utils.check_bing_login():
                        return
            time.sleep(1)