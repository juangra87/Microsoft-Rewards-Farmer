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
        self.utils.read_warnings()

        logging.info(logger_prefix + "Logged-in !")

        self.utils.go_home()
        points = self.utils.get_account_points()

        logging.info(logger_prefix + "Ensuring login on Bing...")
        self.check_bing_login()

        logging.info("[LOGIN] Logged-in successfully !")
        return points

    def execute_login(self):
        logging.info(logger_prefix + "Entering email...")
        email_field = self.getEmailField()

        while True:
            email_field.send_keys(self.browser.username)
            time.sleep(3)
            if email_field.get_attribute("value") == self.browser.username:
                self.submitForm()
                self.utils.try_dismiss_all_messages
                break

            email_field.clear()
            time.sleep(3)
        self.enter_password(self.browser.password)
        time.sleep(1)
        self.utils.try_dismiss_all_messages()
        time.sleep(1)

    def getEmailField(self):
        try:
            email_field = self.webdriver.find_element(By.ID, "i0116")
        except Exception:
            email_field = self.webdriver.find_element(By.ID, "usernameEntry")
        return email_field

    def submitForm(self):
        try:
            self.webdriver.find_element(By.ID, "idSIButton9").click()
        except Exception:
            self.webdriver.find_element(By.CLASS_NAME, "ffp7eso").click()

    def enter_password(self, password):
        try:
            self.utils.wait_until_clickable(By.NAME, "passwd", 10)
        except Exception:
            self.utils.try_dismiss_recovery_email_check()
        self.utils.wait_until_clickable(By.NAME, "passwd", 10)
        password = password.replace("\\", "\\\\").replace('"', '\\"')
        self.webdriver.find_element(By.NAME, "passwd").send_keys(password)
        logging.info("[LOGIN] " + "Writing password...")
        time.sleep(3)
        self.submitForm()

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