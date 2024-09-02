import random
from typing import Any

import requests
from requests import HTTPError, Response


class GenerateUserAgent:
    """A class for generating user agents for Microsoft Rewards Farmer."""

    # Reduced device name, ref: https://developer.chrome.com/blog/user-agent-reduction-android-model-and-version/
    MOBILE_DEVICE = "K"

    USER_AGENT_TEMPLATES = {
        "edge_pc": (
            "Mozilla/5.0"
            " ({system}) AppleWebKit/537.36 (KHTML, like Gecko)"
            " Chrome/{app[chrome_reduced_version]} Safari/537.36"
            " Edg/{app[edge_version]}"
        ),
        "edge_mobile": (
            "Mozilla/5.0"
            " ({system}) AppleWebKit/537.36 (KHTML, like Gecko)"
            " Chrome/{app[chrome_reduced_version]} Mobile Safari/537.36"
            " EdgA/{app[edge_version]}"
        ),
    }

    OS_PLATFORMS = {"win": "Windows NT 10.0", "android": "Linux"}
    OS_CPUS = {"win": "Win64; x64", "android": "Android 10"}

    def user_agent(
        self,
        browser_config: dict[str, Any],
        mobile: bool = False,
    ) -> tuple[str, dict[str, Any], Any]:
        """
        Generates a user agent string for either a mobile or PC device.

        Args:
            mobile: A boolean indicating whether the user agent should be generated for a mobile device.

        Returns:
            A string containing the user agent for the specified device.
        """

        system = self.get_system_components(mobile)
        app = self.get_app_components(mobile)
        ua_template = (
            self.USER_AGENT_TEMPLATES.get("edge_mobile", "")
            if mobile
            else self.USER_AGENT_TEMPLATES.get("edge_pc", "")
        )

        new_browser_config = None
        user_agent_metadata = browser_config.get("userAgentMetadata")
        if not user_agent_metadata:
            # ref : https://textslashplain.com/2021/09/21/determining-os-platform-version/
            platform_version = (
                f"{random.randint(9,13) if mobile else random.randint(1,15)}.0.0"
            )
            new_browser_config = browser_config
            new_browser_config["userAgentMetadata"] = {
                "platformVersion": platform_version,
            }
        else:
            platform_version = user_agent_metadata["platformVersion"]

        ua_metadata = {
            "mobile": mobile,
            "platform": "Android" if mobile else "Windows",
            "fullVersionList": [
                {"brand": "Not/A)Brand", "version": "99.0.0.0"},
                {"brand": "Microsoft Edge", "version": app["edge_version"]},
                {"brand": "Chromium", "version": app["chrome_version"]},
            ],
            "brands": [
                {"brand": "Not/A)Brand", "version": "99"},
                {"brand": "Microsoft Edge", "version": app["edge_major_version"]},
                {"brand": "Chromium", "version": app["chrome_major_version"]},
            ],
            "platformVersion": platform_version,
            "architecture": "" if mobile else "x86",
            "bitness": "" if mobile else "64",
            "model": "",
        }

        return ua_template.format(system=system, app=app), ua_metadata, new_browser_config

    def get_system_components(self, mobile: bool) -> str:
        """
        Generates the system components for the user agent string.

        Args:
            mobile: A boolean indicating whether the user agent should be generated for a mobile device.

        Returns:
            A string containing the system components for the user agent string.
        """
        os_id = self.OS_CPUS.get("android") if mobile else self.OS_CPUS.get("win")
        ua_platform = (
            self.OS_PLATFORMS.get("android") if mobile else self.OS_PLATFORMS.get("win")
        )
        if mobile:
            os_id = f"{os_id}; {self.MOBILE_DEVICE}"
        return f"{ua_platform}; {os_id}"

    def get_app_components(self, mobile: bool) -> dict[str, str]:
        """
        Generates the application components for the user agent string.

        Returns:
            A dictionary containing the application components for the user agent string.
        """
        edge_windows_version, edge_android_version = self.get_edge_versions()
        edge_version = edge_android_version if mobile else edge_windows_version
        edge_major_version = edge_version.split(".")[0]

        chrome_version = self.get_chrome_version()
        chrome_major_version = chrome_version.split(".")[0]
        chrome_reduced_version = f"{chrome_major_version}.0.0.0"

        return {
            "edge_version": edge_version,
            "edge_major_version": edge_major_version,
            "chrome_version": chrome_version,
            "chrome_major_version": chrome_major_version,
            "chrome_reduced_version": chrome_reduced_version,
        }

    def get_edge_versions(self) -> tuple[str, str]:
        """
        Get the latest version of Microsoft Edge.

        Returns:
            str: The latest version of Microsoft Edge.
        """
        response = self.get_webdriver_page(
            "https://edgeupdates.microsoft.com/api/products"
        )
        data = response.json()
        stable_product = next(
            (product for product in data if product["Product"] == "Stable"),
            None,
        )
        if stable_product:
            releases = stable_product["Releases"]
            android_release = next(
                (release for release in releases if release["Platform"] == "Android"),
                None,
            )
            windows_release = next(
                (
                    release
                    for release in releases
                    if release["Platform"] == "Windows"
                    and release["Architecture"] == "x64"
                ),
                None,
            )
            if android_release and windows_release:
                return (
                    windows_release["ProductVersion"],
                    android_release["ProductVersion"],
                )
        raise HTTPError("Failed to get Edge versions.")

    def get_chrome_version(self) -> str:
        """
        Get the latest version of Google Chrome.

        Returns:
            str: The latest version of Google Chrome.
        """
        response = self.get_webdriver_page(
            "https://googlechromelabs.github.io/chrome-for-testing/last-known-good-versions.json"
        )
        data = response.json()
        return data["channels"]["Stable"]["version"]

    @staticmethod
    def get_webdriver_page(url: str) -> Response:
        response = None
        response = requests.get(url)
        if response.status_code != requests.codes.ok:  # pylint: disable=no-member
            raise HTTPError(
                f"Failed to get webdriver page {url}. "
                f"Status code: {response.status_code}"
            )
        return response
