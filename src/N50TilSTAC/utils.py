from pathlib import Path


def get_workdir() -> Path:
    # __file__ is not supported directly in notebooks
    return Path(__file__).parent