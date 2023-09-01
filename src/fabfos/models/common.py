import os, sys
from dataclasses import dataclass
from pathlib import Path

def StripExt(fname: str):
    return ".".join(fname.split(".")[:-1])

def EnsureFolder(p: Path):
    if not p.exists(): os.makedirs(p)
    return p

class Workspace:
    def __init__(self, loc: Path) -> None:
        if not loc.exists(): os.makedirs(loc)
        self._loc = loc

    def GetLogDir(self):
        self.EnsureCache("logs")
        return Path(self._loc).joinpath("logs")

    def EnsureCache(self, name: str):
        dpath = EnsureFolder(self._loc.joinpath(name))
        return dpath
    
    def Gather(self, file: Path, folder_name: str):
        folder = self.EnsureCache(folder_name)
        name, i = file.name, 1
        while True:
            gathered_path = folder.joinpath(name)
            if gathered_path.exists():
                i += 1
                name = f"{file.name}_{i:03}" # in case of duplicate file names, append counter
            else:
                break
        os.symlink(file, gathered_path)
        return gathered_path

    def NewLog(self, name: str, content: str):
        log_dir = self.EnsureCache("logs")
        if not log_dir.exists(): os.makedirs(log_dir)
        with open(log_dir.joinpath(name), "a") as f:
            f.write(content)

@dataclass
class Params:
    threads: int
    workspace: Workspace
    output_prefix: Path
    verbose: bool = False
