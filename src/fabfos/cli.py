import os, sys
import argparse
from pathlib import Path
import logging
from typing import Any
from .constants import GetVersion
from .models.common import Params, Workspace
from .models.pipeline import Toolkit
from .models.data import ReadDirection, ReadSet, GenomicFasta

NAME = "FabFos"
VERSION = f"v{GetVersion()}"
CMD = "ffs"
RUN_DESC = f"{NAME} {VERSION}"

class ArgumentParser(argparse.ArgumentParser):
    def error(self, message):
        self.print_help(sys.stderr)
        self.exit(2, '\n%s: error: %s\n' % (self.prog, message))

####################################################################
# wrap toolkit functions

def _add_default_args(parser: ArgumentParser):
    parser.add_argument("-t", "--threads", metavar="INT", type=int, default=os.cpu_count(), required=False, help="maximum threads to use")
    parser.add_argument("-v", "--verbose", action=argparse.BooleanOptionalAction, help="enable verbose logging")
    parser.add_argument("-w", "--workspace", metavar="PATH", type=Path, default=Path("/tmp/fabfos"), required=False, help="working directory")
    parser.add_argument("-o", "--prefix", metavar="PATH", type=Path, required=True, help="prefix of outputs")
    return parser

def _ensure_path_exists(p: Path):
    if p.exists(): return
    logging.error(f"given path [{p}] doesn't exist")
    os._exit(1)

def ffs_qc(args):
    parser = ArgumentParser(
        prog = f'{CMD} qc',
        description = RUN_DESC,
    )
    parser.add_argument("-1", "--forward", metavar="PATH", type=Path, nargs="+", default=[], required=False, help="forward reads")
    parser.add_argument("-2", "--reverse", metavar="PATH", type=Path, nargs="+", default=[], required=False, help="reverse reads")
    parser.add_argument("-r", "--unpaired", metavar="PATH", type=Path, nargs="+", default=[], required=False, help="unpaired reads")
    parser.add_argument("-b", "--background", metavar="PATH", type=Path, required=True,
        help="the background host genome to filter out")
    parser = _add_default_args(parser)

    raw_params = parser.parse_args(args)

    ws = Workspace(raw_params.workspace)
    params = Params(
        threads = raw_params.threads,
        workspace = ws,
        output_prefix = raw_params.prefix,
    )

    _reads = {}
    raw_params_dict = dict(raw_params._get_kwargs())
    for dir, k in zip(ReadDirection, "forward, reverse, unpaired_reads".split(", ")):
        for read_file in raw_params_dict[k]:
            _ensure_path_exists(read_file)
            _reads[read_file] = dir
    if len(_reads) == 0:
        logging.error(f"no reads provided")
        os._exit(1)

    tk = Toolkit(params)
    tk.QcReads(ReadSet(_reads, params), GenomicFasta(raw_params.background, params))

def ffs_assembly(args):
    parser = ArgumentParser(
        prog = f'{CMD} assembly',
        description = RUN_DESC,
    )
    parser.add_argument("-1", "--forward", metavar="PATH", type=Path, nargs="+", default=[], required=False, help="forward reads")
    parser.add_argument("-2", "--reverse", metavar="PATH", type=Path, nargs="+", default=[], required=False, help="reverse reads")
    parser.add_argument("-r", "--unpaired", metavar="PATH", type=Path, nargs="+", default=[], required=False, help="unpaired reads")
    parser.add_argument("-a", "--assembler", choices=["spades", "megahit", "flye"], default="megahit", required=True, help="assembler")
    parser = _add_default_args(parser)
    parser.add_argument("-m", "--memory", metavar="INT", default=os., required=True, help="assembler")

    raw_params = parser.parse_args(args)

####################################################################
# main entry point

def _get_commands():
    functions_in_scope =  {n:fn for n, fn in globals().items() if callable(fn)}
    return {n.replace(f"{CMD}_", ""):fn for n, fn in functions_in_scope.items() if n.startswith(CMD)}

NEW_LINE = "\n"
MAIN_HELP_TEXT = f"""\
{NAME} {VERSION}
https://github.com/hallamlab/FabFos

Syntax: {CMD} COMMAND [OPTIONS]

Where COMMAND is one of:
help
{NEW_LINE.join(_get_commands())}

for additional help, use:
{CMD} COMMAND -h
"""

def help(cmd=None):
    print(MAIN_HELP_TEXT)
    if cmd is not None and cmd != "help": print(f"COMMAND [{cmd}] not recognized")
   
def EntryPoint():
    if len(sys.argv) <= 1:
        help()
        return

    command_functions = _get_commands()
    cmd = sys.argv[1]
    print(f"{NAME} {VERSION} [{cmd}]")
    command_functions.get(cmd, lambda args: help(cmd))(sys.argv[2:])
    print()
