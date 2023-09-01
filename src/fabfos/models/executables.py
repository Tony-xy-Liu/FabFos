import os, sys
from enum import Enum, auto
import subprocess
import logging

from fabfos.models.common import Workspace

class Executable(Enum):
    SAMTOOLS = "samtools"
    BWA = "bwa"
    TRIMMOMATIC = "trimmomatic"

    def __str__(self) -> str:
        return self.value

def Shell(cmd: str):
    proc = subprocess.Popen(cmd, shell=True, preexec_fn=os.setsid, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    stdout = proc.communicate()[0].decode("utf-8")
    return stdout, proc.returncode

def Run(cmd: str, workspace: Workspace, run_name: str, exit_on_fail: bool=True):
    stdout, code = Shell(cmd)
    workspace.NewLog(run_name, f"{cmd.replace('    ', ' ')}\n\n{stdout}")
    is_success = code == 0
    if not is_success:
        NL = "\n"
        logging.error(f"External dependency did not complete successfully! Command used:{NL}{cmd}")
        if exit_on_fail:
            sys.exit(19)
    return is_success
