import os
from pathlib import Path


def get_workdir() -> Path:
    # __file__ is not supported directly in notebooks
    return Path(__file__).parent


def create_dir(name: str):
    try:
        os.mkdir(name)
        print(f"Directory '{name}' created successfully.")
    except FileExistsError:
        print(f"Directory '{name}' already exists.")
    except PermissionError:
        print(f"Permission denied: Unable to create '{name}'.")
    except Exception as e:
        print(f"An error occurred: {e}")