import os, sys
from pathlib import Path

HERE = Path(os.getcwd())
sys.path = list(set([
    HERE.joinpath("src"),
]+sys.path))

if __name__ == "__main__":
    from fabfos.cli import EntryPoint
    EntryPoint()
