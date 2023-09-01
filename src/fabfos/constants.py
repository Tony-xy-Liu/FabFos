import os, sys
from pathlib import Path

SRC_DIR = Path(os.path.realpath(__file__)).parent

_version = None
def GetVersion():
    global _version
    if _version is None:
        try:
            with open(SRC_DIR.joinpath("version.txt")) as f:
                _version = f.readline()
        except FileNotFoundError:
            _version = "-.-.-"
    return _version
