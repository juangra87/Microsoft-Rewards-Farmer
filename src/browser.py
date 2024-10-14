import contextlib
import logging
import random
import uuid
from pathlib import Path
from typing import Any

import ipapi
import seleniumwire.undetected_chromedriver as webdriver
from selenium.webdriver.chrome.webdriver import WebDriver

from src.userAgentGenerator import GenerateUserAgent
from src.utils import Utils


DEFAULT_SLEEP = 80
class Browser:
    """WebDriver wrapper class."""

    def __init__(self, mobile: bool, account, args: Any) -> None:
        self.mobile = mobile
        self.browser_type = "mobile" if mobile else "desktop"
        self.headless = not args.visible
        self.username = account["username"]
        self.password = account["password"]
        try:
            self.sleep = account["sleep"]
        except Exception:
            self.sleep = DEFAULT_SLEEP
        logging.info(
            f'[BROWSER] { self.sleep } seconds between searches '
        )
        self.locale_lang, self.locale_geo = self.get_c_code_lang(args.lang, args.geo)
        self.proxy = None
        if args.proxy:
            self.proxy = args.proxy
        elif account.get("proxy"):
            self.proxy = account["proxy"]
        self.user_data_dir = self.setup_profiles()
        self.browser_config = Utils.get_browser_config(self.user_data_dir)
        (
            self.user_agent,
            self.user_agent_metadata,
            new_browser_config,
        ) = GenerateUserAgent().user_agent(self.browser_config, mobile)
        if new_browser_config:
            self.browser_config = new_browser_config
            Utils.save_browser_config(self.user_data_dir, self.browser_config)
        self.webdriver = self.browser_setup()
        self.utils = Utils(self.webdriver)

    def __enter__(self) -> "Browser":
        return self

    def __exit__(self, *args: Any) -> None:
        self.close_browser()

    def close_browser(self) -> None:
        """Perform actions to close the browser cleanly."""
        # close web browser
        with contextlib.suppress(Exception):
            self.webdriver.close()
            self.webdriver.quit()

    def browser_setup(
        self,
    ) -> WebDriver:
        options = webdriver.ChromeOptions()
        options.headless = self.headless
        options.add_argument(f"--lang={self.locale_lang}")
        options.add_argument("--log-level=3")

        options.add_argument("--ignore-certificate-errors")
        options.add_argument("--ignore-certificate-errors-spki-list")
        options.add_argument("--ignore-ssl-errors")
        options.add_argument("--disable-search-engine-choice-screen")

        selenium_options: dict[str, Any] = {"verify_ssl": False}

        if self.proxy:
            selenium_options["proxy"] = {
                "http": self.proxy,
                "https": self.proxy,
                "no_proxy": "localhost,127.0.0.1",
            }

        driver = webdriver.Chrome(
            options=options,
            seleniumwire_options=selenium_options,
            user_data_dir=self.user_data_dir.as_posix(),
        )

        selenium_logger = logging.getLogger("seleniumwire")
        selenium_logger.setLevel(logging.ERROR)

        if self.browser_config.get("sizes"):
            device_height = self.browser_config["sizes"]["height"]
            device_width = self.browser_config["sizes"]["width"]
        else:
            if self.mobile:
                device_height = random.randint(568, 1024)
                device_width = random.randint(320, min(576, int(device_height * 0.7)))
            else:
                device_width = random.randint(1024, 2560)
                device_height = random.randint(768, min(1440, int(device_width * 0.8)))
            self.browser_config["sizes"] = {
                "height": device_height,
                "width": device_width,
            }
            Utils.save_browser_config(self.user_data_dir, self.browser_config)

        if self.mobile:
            screen_height = device_height + 146
            screen_width = device_width
        else:
            screen_width = device_width + 55
            screen_height = device_height + 151

        logging.info(f"Screen size: {screen_width}x{screen_height}")
        logging.info(f"Device size: {device_width}x{device_height}")

        if self.mobile:
            driver.execute_cdp_cmd(
                "Emulation.setTouchEmulationEnabled",
                {
                    "enabled": True,
                },
            )

        driver.execute_cdp_cmd(
            "Emulation.setDeviceMetricsOverride",
            {
                "width": device_width,
                "height": device_height,
                "deviceScaleFactor": 0,
                "mobile": self.mobile,
                "screenWidth": screen_width,
                "screenHeight": screen_height,
                "positionX": 0,
                "positionY": 0,
                "viewport": {
                    "x": 0,
                    "y": 0,
                    "width": device_width,
                    "height": device_height,
                    "scale": 1,
                },
            },
        )

        driver.execute_cdp_cmd(
            "Emulation.setUserAgentOverride",
            {
                "userAgent": self.user_agent,
                "platform": self.user_agent_metadata["platform"],
                "userAgentMetadata": self.user_agent_metadata,
            },
        )
        # Set timeout to something bigger that account sleep
        timeout = self.sleep + 5
        logging.info(
            f'[BROWSER] Default timeout:{timeout}'
        )
        driver.set_page_load_timeout(timeout)
        return driver

    def setup_profiles(self) -> Path:
        """
        Sets up the sessions profile for the chrome browser.
        Uses the username to create a unique profile for the session.

        Returns:
            Path
        """
        current_path = Path(__file__)
        parent = current_path.parent.parent
        sessions_dir = parent / "sessions"

        session_uuid = uuid.uuid5(uuid.NAMESPACE_DNS, self.username)
        sessions_dir = sessions_dir / str(session_uuid) / self.browser_type
        sessions_dir.mkdir(parents=True, exist_ok=True)
        return sessions_dir

    def get_c_code_lang(self, lang: str, geo: str) -> tuple:
        if lang is None or geo is None:
            try:
                nfo = ipapi.location()
                if isinstance(nfo, dict):
                    if lang is None:
                        lang = nfo["languages"].split(",")[0].split("-")[0]
                    if geo is None:
                        geo = nfo["country"]
            except Exception:  # pylint: disable=broad-except
                return ("en", "US")
        return (lang, geo)
