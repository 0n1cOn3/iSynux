from os.path import expanduser, join
from os import environ
from getpass import getpass
from pyicloud.services.drive import DriveNode


USERNAME_CACHE_FILE = expanduser("~/.username")


def get_input_or_fallback_file(prompt: str, fallback_file: str):
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


def get_credentials(password_already_saved: bool):
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


def upload_file_to_icloud(file_path: str, icloud_folder: DriveNode) -> None:
    filename = Path(file_path).name
    with open(file_path, 'rb') as file:
        icloud_folder.upload(filename, file)
