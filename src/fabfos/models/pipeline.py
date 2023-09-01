from __future__ import annotations
import os
from enum import Enum, auto
from dataclasses import dataclass
from pathlib import Path
import logging
import shutil
from .data import GenomicFasta, ReadDirection, ReadSet
from .common import Params, Workspace, EnsureFolder


class Toolkit:
    def __init__(self, params: Params) -> None:
        self._params = params
        os.chdir(params.workspace._loc)

    def Deinterleave(self, fastq: Path):
        pass

    def QcReads(self, reads: ReadSet, background: GenomicFasta):
        params = self._params
        _prep_logging(params.workspace.GetLogDir().joinpath("main_qc.log"), params.verbose)
        
        reads.Count("original")
        reads.Filter(background)
        reads.Count("filtered")
        reads.Trim()
        reads.Count("trimmed")

        out_dir = EnsureFolder(params.output_prefix.parent)
        prefix = params.output_prefix.name
        suffix_map = {
            ReadDirection.FORWARD: "R1",
            ReadDirection.REVERSE: "R2",
            ReadDirection.SINGLE: "single",
        }
        for rdir, suffix in suffix_map.items():
            read_files = [r for r, d in reads.Files.items() if d == rdir]
            if len(read_files) == 0: continue
            if len(read_files) == 1:
                shutil.copy(read_files[0], out_dir.joinpath(f"{prefix}_{suffix}.fq"))
            else:
                for i, f in enumerate(read_files):
                    shutil.copy(f, out_dir.joinpath(f"{prefix}_{i+1:03}_{suffix}.fq"))
        for k, (reads, nucleotides) in reads.CountStats.items():
            logging.info(f"{k}:\t{reads} reads,\t{nucleotides} nucleoties")
        
    def EstimatePoolSize(self):
        pass

    def AssemblePool(self):
        pass

    def MapEnds(self):
        pass

    def SummaryFigures(self):
        pass

class _MyFormatter(logging.Formatter):

    error_fmt = "%(levelname)s - %(module)s, line %(lineno)d:\n%(message)s"
    warning_fmt = "%(levelname)s:\n%(message)s"
    debug_fmt = "%(asctime)s\n%(message)s"
    info_fmt = "%(message)s\n"

    def __init__(self):
        super().__init__(fmt="%(levelname)s: %(message)s",
                         datefmt="%d/%m %H:%M:%S")

    def format(self, record):

        # Save the original format configured by the user
        # when the logger formatter was instantiated
        format_orig = self._style._fmt

        # Replace the original format with one customized by logging level
        if record.levelno == logging.DEBUG:
            self._style._fmt = _MyFormatter.debug_fmt

        elif record.levelno == logging.INFO:
            self._style._fmt = _MyFormatter.info_fmt

        elif record.levelno == logging.ERROR:
            self._style._fmt = _MyFormatter.error_fmt

        elif record.levelno == logging.WARNING:
            self._style._fmt = _MyFormatter.warning_fmt

        # Call the original formatter class to do the grunt work
        result = logging.Formatter.format(self, record)

        # Restore the original format configured by the user
        self._style._fmt = format_orig
        return result
    
def _prep_logging(log_path: Path, verbose=False):
    logging.basicConfig(level=logging.DEBUG,
                        filename=log_path,
                        filemode='w',
                        datefmt="%d/%m %H:%M:%S",
                        format="%(asctime)s %(levelname)s:\n%(message)s")
    if verbose:
        logging_level = logging.DEBUG
    else:
        logging_level = logging.INFO

    # Set the console handler normally writing to stdout/stderr
    ch = logging.StreamHandler()
    ch.setLevel(logging_level)
    ch.terminator = ''

    formatter = _MyFormatter()
    ch.setFormatter(formatter)
    logging.getLogger('').addHandler(ch)
    return

