"""
This file is part of SEE Lang Detector
and falls under the license
Attribution-NonCommercial-NoDerivatives 4.0 International.
"""

import json
import logging

import qtpy.QtCore as qtc
import requests
import semantic_version as semver

from main import MainApp


class Updater(qtc.QObject):
    """
    Class for updating application.
    """

    repo_name = "SSE-Lang-Detector"
    repo_owner = "Cutleast"

    installed_version: semver.Version = None
    latest_version: semver.Version = None
    download_url: str = None

    def __init__(self, app: MainApp):
        super().__init__()

        self.app = app
        self.installed_version = semver.Version(self.app.version)
        self.log = logging.getLogger(self.__repr__())
        self.log.addHandler(app.log_str)
        self.log.setLevel(app.log.level)

        self.log.info("Checking for update...")
        if self.update_available():
            self.log.info(
                f"Update available: Installed: {self.installed_version} - Latest: {self.latest_version}"
            )

            from .updater_dialog import UpdaterDialog

            UpdaterDialog(app, self)
        else:
            self.log.info("No update available.")

    def __repr__(self):
        return "Updater"

    def update_available(self) -> bool:
        """
        Checks if update is available and returns True or False.

        Returns False if requested version is invalid.
        """

        self.request_update()

        if self.latest_version is None:
            return False

        return self.installed_version < self.latest_version

    def request_update(self):
        """
        Requests latest available version and download url
        from GitHub repository.
        """

        url = f"https://raw.githubusercontent.com/{self.repo_owner}/{self.repo_name}/main/update.json"
        response = requests.get(url, timeout=3)
        if response.status_code == 200:
            latest_version_json = response.content.decode(encoding="utf8", errors="ignore")
            latest_version_data = json.loads(latest_version_json)
            latest_version = latest_version_data["version"]
            self.latest_version = semver.Version(latest_version)
            self.download_url = latest_version_data["download_url"]
        else:
            self.log.error(f"Failed to request update. Status Code: {response.status_code}")
            self.log.debug(f"Request URL: {url}")

    def get_changelog(self):
        """
        Gets changelog from repository.

        Returns it as string with markdown.
        """

        url = f"https://raw.githubusercontent.com/{self.repo_owner}/{self.repo_name}/main/Changelog.md"
        response = requests.get(url, timeout=3)

        if response.status_code == 200:
            changelog = response.content.decode(encoding="utf8", errors="ignore")

            return changelog
        else:
            self.log.error(f"Failed to request changelog. Status Code: {response.status_code}")
            self.log.debug(f"Request URL: {url}")

            return f"Status Code: {response.status_code}"
        
