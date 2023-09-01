from dataclasses import dataclass
import logging
from pathlib import Path
from fabfos.models import Params, ReadDir, Workspace

@dataclass
class QcParams:
    background: Path
    reads: list[tuple[ReadDir, Path]]

class QcState:
    pass

def QcReads(params: Params, background: str, parity: str, adapters: str, executables: dict, num_threads=2) -> None:
    ws = params.workspace
    
    filtered_reads = _filter_backbone(self, background, executables, parity, num_threads)
    self.read_stats.num_filtered_reads = find_num_reads(filtered_reads)
    self.read_stats.calc_on_target()
    logging.info("{0} reads removed by filtering background ({1}%).\n".format(self.read_stats.num_on_target,
                                                                                self.read_stats.percent_on_target()))
    if self.read_stats.num_filtered_reads < 1600:
        # The number of reads remaining is too low for assembly (< 20X for a single fosmid)
        logging.warning("Number of reads remaining will provide less than 20X coverage for a single fosmid"
                        " - skipping this sample\n")
        return
    trimmed_reads = quality_trimming(executables["trimmomatic"], self, filtered_reads, parity, adapters, num_threads)
    self.read_stats.num_reads_assembled = find_num_reads(trimmed_reads)
    self.read_stats.num_reads_trimmed = self.read_stats.num_filtered_reads - self.read_stats.num_reads_assembled

    self.prep_reads_for_assembly(trimmed_reads)
    return