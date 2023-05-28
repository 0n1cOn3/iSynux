#!/bin/python3
from getpass import getpass
import json
from re import A
import click
import sys
from pyicloud import PyiCloudService
from os.path import expanduser
from os import environ

USERNAME_CACHE_FILE = ".username"


def get_input_or_fallback_file(prompt, fallback_file):
    try:
        f = open(fallback_file, "r")
        username = f.read()
        f.close()
    except FileNotFoundError:
        username = input(prompt)

        f = open(fallback_file, "w")
        f.write(username)
        f.close()

    return username


def get_credinteals(password_already_saved: bool):
    username = get_input_or_fallback_file("Email: ", USERNAME_CACHE_FILE)
    if password_already_saved:
        return username, ""
    return username, getpass(f"Password for {username}: ")


def ask_yes_or_no(question_string: str, prefer_true: bool) -> bool:
    if prefer_true:
        return input(question_string + "[Y/n]: ").lower() != "n"
    return input(question_string + " [y/N]: ").lower == "y"


def get_env(key: str) -> str:
    try:
        return environ[key]
    except KeyError:
        return ""


def authenticate_2fa(api: PyiCloudService) -> int:
    if api.requires_2fa:
        code = input(
            "Enter the code you received of one of your approved devices: ")
        result = api.validate_2fa_code(code)

        if not result:
            print("Failed to verify security code")
            return 1

        if not api.is_trusted_session:
            print("Session is not trusted. Requesting trust...")
            result = api.trust_session()
            print("Session trust result %s" % result)

            if not result:
                print(
                    "Failed to request trust. You will likely be prompted for the code again in the coming weeks")
    elif api.requires_2sa:
        print("Two-step authentication required. Your trusted devices are:")

        devices = api.trusted_devices
        for i, device in enumerate(devices):
            print(
                "  %s: %s" % (i, device.get('deviceName',
                                            "SMS to %s" % device.get('phoneNumber')))
            )

        device = click.prompt('Which device would you like to use?', default=0)
        device = devices[device]
        if not api.send_verification_code(device):
            print("Failed to send verification code")
            return 1

        code = click.prompt('Please enter validation code')
        if not api.validate_verification_code(device, code):
            print("Failed to verify verification code")
            return 1

    return 0


def list_files_recursive(folder, current_path=""):
    files = folder.get_children()
    if not files:
        return []

    for file in files:
        if file.type == "folder" or file.type == "app_directory":
            new_path = f"{current_path}/{file.name}" if current_path else file.name
            list_files_recursive(file, new_path)
        elif file.type == "file":
            file_path = f"{current_path}/{file.name}" if current_path else file.name
            print(file_path)


def sync_icloud_files_to(api: PyiCloudService, sync_dir: str):
    # Retrieve the root folder from iCloud Drive
    root_folder = api.drive.root
    list_files_recursive(root_folder, "")


def main() -> int:
    has_password_been_saved_to_keyring = get_env("PYICLOUD_PASSWORD") != ""
    username, password = get_credinteals(has_password_been_saved_to_keyring)

    if has_password_been_saved_to_keyring:
        api = PyiCloudService(username)
    else:
        api = PyiCloudService(username, password)

    if authenticate_2fa(api) > 0:
        return 1

    sync_dir = expanduser("~/.icloud-sync")
    if len(sys.argv) > 1:
        sync_dir = sys.argv[1]

    sync_icloud_files_to(api, sync_dir)

    return 0


if __name__ == "__main__":
    status_code = main()
    sys.exit(status_code)
