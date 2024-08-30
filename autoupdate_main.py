import os
import sys
from io import BytesIO
from zipfile import ZipFile

import requests


def update(version: str):
    url = "https://github.com/charlesbel/Microsoft-Rewards-Farmer/archive/refs/heads/master.zip"
    folder_name = "Microsoft-Rewards-Farmer-master"
    with open(".gitignore", "r") as f:
        exclusions = f.read().splitlines()
        exclusions = [e for e in exclusions if e != "" and not e.startswith("#")] + [
            ".gitignore",
            ".git",
        ]
    print("Removing old files...")
    for root, dirs, files in os.walk(".", topdown=False):
        for name in files:
            path = os.path.join(root, name)
            relative_path = path[2:]
            if not relative_path.startswith(tuple(exclusions)):
                os.remove(path)
    print("Downloading...")
    r = requests.get(url)
    data = BytesIO(r.content)
    print("Extracting...")
    with ZipFile(data, "r") as zipObj:
        files = [
            f
            for f in zipObj.namelist()
            if f.startswith(folder_name) and not f.endswith("/")
        ]
        for file in files:
            new_name = file.replace(f"{folder_name}/", "")
            dir_name = os.path.dirname(new_name)
            if "/" in new_name and not os.path.exists(dir_name):
                print(f"Creating folder {dir_name}...")
                os.makedirs(dir_name)
            with zipObj.open(file) as src, open(new_name, "wb") as dst:
                dst.write(src.read())
    with open('version.txt', "w") as f:
        f.write(version)
    print("Done !")


def get_current_version():
    if os.path.exists("version.txt"):
        with open("version.txt", "r") as f:
            version = f.read()
        return version
    return None


def get_latest_version():
    r = requests.get(
        "https://api.github.com/repos/charlesbel/Microsoft-Rewards-Farmer/commits/master"
    )
    return r.json()["sha"]


if __name__ == "__main__":
    currentVersion = get_current_version()
    latestVersion = get_latest_version()
    if currentVersion != latestVersion:
        print("New version available !")
        update(latestVersion)

    print("Starting...")

    import main

    main.sys.argv[1:] = sys.argv[1:]
    main.main()
