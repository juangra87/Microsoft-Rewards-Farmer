import contextlib
import json
import locale as pylocale
import time
import urllib.parse
from pathlib import Path
import logging

import requests
from requests.adapters import HTTPAdapter
from selenium.webdriver.chrome.webdriver import WebDriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as ec
from selenium.webdriver.support.wait import WebDriverWait
from requests import Session
from urllib3 import Retry

from .constants import BASE_URL


class Utils:
    def __init__(self, webdriver: WebDriver):
        self.webdriver = webdriver
        with contextlib.suppress(Exception):
            locale = pylocale.getdefaultlocale()[0]
            pylocale.setlocale(pylocale.LC_NUMERIC, locale)

    def wait_until_visible(self, by: str, selector: str, time_to_wait: float = 10):
        WebDriverWait(self.webdriver, time_to_wait).until(
            ec.visibility_of_element_located((by, selector))
        )

    def wait_until_clickable(self, by: str, selector: str, time_to_wait: float = 10):
        WebDriverWait(self.webdriver, time_to_wait).until(
            ec.element_to_be_clickable((by, selector))
        )

    def wait_for_ms_reward_element(self, by: str, selector: str):
        loading_time_allowed = 5
        refreshs_allowed = 5

        checking_interval = 0.5
        checks = loading_time_allowed / checking_interval

        tries = 0
        refresh_count = 0
        while True:
            try:
                self.webdriver.find_element(by, selector)
                return True
            except Exception:  # pylint: disable=broad-except
                if tries < checks:
                    tries += 1
                    time.sleep(checking_interval)
                elif refresh_count < refreshs_allowed:
                    self.webdriver.refresh()
                    refresh_count += 1
                    tries = 0
                    time.sleep(5)
                else:
                    return False

    def wait_until_question_refresh(self):
        return self.wait_for_ms_reward_element(By.CLASS_NAME, "rqECredits")

    def wait_until_quiz_loads(self):
        return self.wait_for_ms_reward_element(By.XPATH, '//*[@id="rqStartQuiz"]')

    def reset_tabs(self):
        try:
            curr = self.webdriver.current_window_handle

            for handle in self.webdriver.window_handles:
                if handle != curr:
                    self.webdriver.switch_to.window(handle)
                    time.sleep(0.5)
                    self.webdriver.close()
                    time.sleep(0.5)

            self.webdriver.switch_to.window(curr)
            time.sleep(0.5)
            self.go_home()
        except Exception:  # pylint: disable=broad-except
            self.go_home()

    def go_home(self):
        reload_threshold = 5
        reload_interval = 10
        target_url = urllib.parse.urlparse(BASE_URL)
        self.webdriver.get(BASE_URL)
        reloads = 0
        interval = 1
        interval_count = 0
        while True:
            self.try_dismiss_cookie_banner()
            with contextlib.suppress(Exception):
                self.webdriver.find_element(By.ID, "more-activities")
                break
            current_url = urllib.parse.urlparse(self.webdriver.current_url)
            if (
                current_url.hostname != target_url.hostname
            ) and self.try_dismiss_all_messages():
                time.sleep(1)
                self.webdriver.get(BASE_URL)
            time.sleep(interval)
            interval_count += 1
            if interval_count >= reload_interval:
                interval_count = 0
                reloads += 1
                self.webdriver.refresh()
                if reloads >= reload_threshold:
                    break

    def get_answer_code(self, key: str, string: str) -> str:
        t = sum(ord(string[i]) for i in range(len(string)))
        t += int(key[-2:], 16)
        return str(t)

    def get_dashboard_data(self) -> dict:
        return self.webdriver.execute_script("return dashboard")

    def get_bing_info(self):
        cookie_jar = self.webdriver.get_cookies()
        cookies = {cookie["name"]: cookie["value"] for cookie in cookie_jar}
        tries = 0
        max_tries = 5
        while tries < max_tries:
            with contextlib.suppress(Exception):
                response = requests.get(
                    "https://www.bing.com/rewards/panelflyout/getuserinfo",
                    cookies=cookies,
                )
                if response.status_code == requests.codes.ok:
                    data = response.json()
                    return data
            tries += 1
            time.sleep(1)
        return None

    def check_bing_login(self):
        data = self.get_bing_info()
        if data:
            return data["userInfo"]["isRewardsUser"]
        else:
            return False

    def get_account_points(self) -> int:
        return self.get_dashboard_data()["userStatus"]["availablePoints"]

    def get_bing_account_points(self) -> int:
        data = self.get_bing_info()
        if data:
            return data["userInfo"]["balance"]
        else:
            return 0

    def try_dismiss_all_messages(self):
        buttons = [
            (By.ID, "iLandingViewAction"),
            (By.ID, "iShowSkip"),
            (By.ID, "iNext"),
            (By.ID, "iLooksGood"),
            (By.ID, "idSIButton9"),
            (By.CSS_SELECTOR, ".ms-Button.ms-Button--primary"),
        ]
        result = False
        for button in buttons:
            try:
                self.webdriver.find_element(button[0], button[1]).click()
                result = True
            except Exception:  # pylint: disable=broad-except
                continue
        return result

    def try_dismiss_cookie_banner(self):
        with contextlib.suppress(Exception):
            self.webdriver.find_element(By.ID, "cookie-banner").find_element(
                By.TAG_NAME, "button"
            ).click()
            time.sleep(2)

    def try_dismiss_bing_cookie_banner(self):
        with contextlib.suppress(Exception):
            self.webdriver.find_element(By.ID, "bnp_btn_accept").click()
            time.sleep(2)

    def switch_to_new_tab(self, time_to_wait: int = 0):
        time.sleep(0.5)
        self.webdriver.switch_to.window(window_name=self.webdriver.window_handles[1])
        if time_to_wait > 0:
            time.sleep(time_to_wait)

    def close_current_tab(self):
        self.webdriver.close()
        time.sleep(0.5)
        self.webdriver.switch_to.window(window_name=self.webdriver.window_handles[0])
        time.sleep(0.5)

    def visit_new_tab(self, time_to_wait: int = 0):
        self.switch_to_new_tab(time_to_wait)
        self.close_current_tab()

    def get_remaining_searches(self):
        dashboard = self.get_dashboard_data()
        search_points = 1
        counters = dashboard["userStatus"]["counters"]
        if "pcSearch" not in counters:
            return 30, 20

        progress_desktop = 0
        target_desktop = 0
        for counter in counters["pcSearch"]:
            progress_desktop += counter["pointProgress"]
            target_desktop += counter["pointProgressMax"]
        logging.info(f"[REMAINING POINTS FROM SEARCHES]: {target_desktop - progress_desktop}")

        if target_desktop in [30, 102, 90]:
            # Level 1 or 2 EU
            search_points = 3
        elif target_desktop == 55 or target_desktop >= 170:
            # Level 1 or 2 US
            search_points = 5
        remaining_desktop = int((target_desktop - progress_desktop) / search_points)
        remaining_mobile = 0
        if dashboard["userStatus"]["levelInfo"]["activeLevel"] != "Level1":
            progress_mobile = counters["mobileSearch"][0]["pointProgress"]
            target_mobile = counters["mobileSearch"][0]["pointProgressMax"]
            remaining_mobile = int((target_mobile - progress_mobile) / search_points)
        return remaining_desktop, remaining_mobile

    def format_number(self, number, num_decimals=2):
        return pylocale.format_string(
            f"%10.{num_decimals}f", number, grouping=True
        ).strip()

    @staticmethod
    def make_requests_session(session: Session = requests.session()) -> Session:
        retry = Retry(
            total=5, backoff_factor=0.1, status_forcelist=[500, 502, 503, 504]
        )
        session.mount(
            "https://", HTTPAdapter(max_retries=retry)
        )  # See https://stackoverflow.com/a/35504626/4164390 to finetune
        session.mount(
            "http://", HTTPAdapter(max_retries=retry)
        )  # See https://stackoverflow.com/a/35504626/4164390 to finetune
        return session

    @staticmethod
    def get_browser_config(session_path: Path) -> dict:
        config_file = session_path.joinpath("config.json")
        if config_file.exists():
            with open(config_file, "r") as f:
                config = json.load(f)
                return config
        else:
            return {}

    @staticmethod
    def save_browser_config(session_path: Path, config: dict):
        config_file = session_path.joinpath("config.json")
        with open(config_file, "w") as f:
            json.dump(config, f)
