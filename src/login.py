import contextlib
import logging
import time

from selenium.webdriver.common.by import By

from src.browser import Browser


class Login:
    def __init__(self, browser: Browser):
        self.browser = browser
        self.webdriver = browser.webdriver
        self.utils = browser.utils

    def login(self):
        logging.info("[LOGIN] " + "Logging-in...")
        self.webdriver.get( "https://rewards.bing.com/Signin/")
        alreadyLoggedIn = False

        if not alreadyLoggedIn:
            self.executeLogin()
        self.utils.tryDismissCookieBanner()

        logging.info("[LOGIN] " + "Logged-in !")

        self.utils.goHome()
        points = self.utils.getAccountPoints()

        logging.info("[LOGIN] Logged-in successfully !")
        return points

    def executeLogin(self):
        logging.info("[LOGIN] " + "Entering email...")
        self.utils.waitUntilClickable(By.NAME, "loginfmt", 10)
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
            self.enterPassword(self.browser.password)
        except Exception:  # pylint: disable=broad-except
            logging.error("[LOGIN] " + "2FA required !")
            with contextlib.suppress(Exception):
                try:
                    code = self.webdriver.find_element(By.ID, "idRemoteNGC_DisplaySign").get_attribute("innerHTML")
                except Exception:  # pylint: disable=broad-except
                    code = self.webdriver.find_element(By.ID, "displaySign").get_attribute("innerHTML")
                    with contextlib.suppress(Exception):
                        logging.error("[LOGIN] " + f"2FA code: {code}")
            
            
            logging.info("[LOGIN] " + "Waiting for 2FA code...")            
            logging.info("[LOGIN] Press enter when confirmed...")
            input()

        self.utils.tryDismissAllMessages()
        time.sleep(1)

    def enterPassword(self, password):
        self.utils.waitUntilClickable(By.NAME, "passwd", 10)
        self.utils.waitUntilClickable(By.ID, "idSIButton9", 10)
        password = password.replace("\\", "\\\\").replace('"', '\\"')
        self.webdriver.find_element(By.NAME, "passwd").send_keys(password)
        logging.info("[LOGIN] " + "Writing password...")
        time.sleep(3)
        self.webdriver.find_element(By.ID, "idSIButton9").click()
