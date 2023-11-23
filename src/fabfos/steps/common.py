import os, sys
from pathlib import Path
from dataclasses import dataclass
import logging
import json
from typing import Callable, Iterable

from ..models import ReadsManifest
from ..process_management import Shell, ShellResult

@dataclass
class Context:
    threads: int
    expected_output: Path
    out_dir: Path
    root_workspace: Path
    log: logging.Logger
    log_file: Path
    args: list[str]
    params: dict
    shell: Callable[[str], ShellResult]

    _i = -1
    def NextArg(self):
        self._i += 1
        return self.args[self._i]

def Init(args, name: str, level=logging.INFO):
    N = 2
    threads, output = args[:N]
    out_dir = Path(output).parent
    if not out_dir.exists(): os.makedirs(out_dir)
    ws = Path(".").absolute()
    with open(ws.joinpath("params.json")) as j:
        params = json.load(j)
    log_file = ws.joinpath(f"logs/{name}.log")
    logging.basicConfig(
        filename=str(log_file),
        filemode='a',
        format='%(asctime)s %(levelname)s: %(message)s',
        datefmt='%H:%M:%S',
        level=level
    )
    log = logging.getLogger('step_logger')
    log.info(f"")
    log.info(f"")
    log.info(f"-- START --")
    log.addHandler(logging.StreamHandler(sys.stderr))
    threads = int(threads)
    return Context(
        threads=threads,
        expected_output=Path(output),
        out_dir=out_dir,
        root_workspace=ws,
        log=log,
        log_file=log_file,
        args=args[N:],
        params=params,
        shell=lambda cmd: Shell(cmd, on_out=log.info, on_err=log.error)
    )

def FileSafeStr(s: str):
    WL = "-_."
    return "".join(ch if (ch.isalnum() or ch in WL) else "_" for ch in s)

def Batchify(it: Iterable, size: int =1):
    lst = list(it)
    l = len(lst)
    for ndx in range(0, l, size):
        yield lst[ndx:min(ndx + size, l)]

def Suffix(file: str, suf: str, cut=0):
    toks = file.split('.')
    name = '.'.join(toks[:-1-cut])
    ext = toks[-1]
    return f"{name}{suf}.{ext}"

def AggregateReads(fwd, rev, single, out_dir):
    aggregates: dict[str, list[Path]] = dict(forward=[], reverse=[], interleaved=[], single=[])
    def _untemp(p: Path):
        if out_dir not in p.parents: return p
        name = p.name.removeprefix("temp.")
        newp = p.parent.joinpath(name)
        os.system(f"mv {p} {newp}")
        return newp
        
    for files, name, out in [
        (fwd, "forward", "fwd.fq"),
        (rev, "reverse", "rev.fq"),
        (single, "single", "se.fq"),
    ]:
        if len(files) < 2:
            if len(files) == 1: 
                files = [_untemp(files[0])]
            aggregates[name]=files
        else:
            agg = out_dir.joinpath(out)
            aggregates[name]=[agg]
            for r in files:
                os.system(f"cat {r} >> {agg}")
    return ReadsManifest(**aggregates)

def ClearTemp(folder: Path):
    if any(f.startswith("temp") for f in os.listdir(folder)):
        os.system(f"rm -r {folder}/temp*")
