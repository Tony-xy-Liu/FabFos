import os, sys
from pathlib import Path
import logging
import subprocess
from enum import Enum, auto

from .common import Params, StripExt
from .executables import Executable, Run, Shell

class ReadDirection(Enum):
    FORWARD = auto()
    REVERSE = auto()
    SINGLE = auto()

class GenomicFasta:
    def __init__(self, file: Path, params: Params) -> None:
        self._params = params
        self.Original = file
        self.Fasta = params.workspace.Gather(file, "genomic_fastas")

    def __str__(self) -> str:
        return f"{self.Fasta}"

    def EnsureBwaIndex(self) -> bool:
        reference = self.Fasta
        extensions = ['.bwt', '.pac', '.ann', '.amb', '.sa']
        index_files = [reference.joinpath(e) for e in extensions]
        if all(i.exists() for i in index_files): return True
        
        logging.info(f"Indexing [{reference.name}]")
        log_name = f"bwa_index--{StripExt(reference.name)}.log"
        cmd = f"{Executable.BWA} index {reference}"
        return Run(cmd, self._params.workspace, log_name)

class ReadSet:
    def __init__(self, files: dict[Path, ReadDirection], params: Params) -> None:
        self.Originals = files
        self._params = params
        folder = params.workspace.EnsureCache("sequence_reads")
        self.Folder = folder
        
        _reads = {}
        _dirs = set()
        for f, read_direction in files.items():
            fpath = params.workspace.Gather(f, folder.name)
            _reads[fpath] = read_direction
            _dirs.add(read_direction)
        self.Files = _reads
        self.pe = len(_dirs)>1
        self.CountStats = {}

    # counts current number of reads and nucleotides
    def Count(self, key: str):
        num_reads, nucleotides = 0, 0
        for f in self.Files:
            stdout, _ = Shell(f"cat {f} | awk 'NR % 4 == 2' | wc -cl")
            toks = stdout[:-1].strip()
            if "\t" in toks: toks = toks.split("\t")
            else: toks = [t for t in toks.split(" ") if len(t)>0]
            nr, nuc = [int(t) for t in toks]
            num_reads += nr
            nucleotides += nuc
        self.CountStats[key] = num_reads, nucleotides

    # align reads against reference (@background) fasta and extract unaligned reads
    def Filter(self, background: GenomicFasta):
        background.EnsureBwaIndex()

        params = self._params
        folder = self.Folder
        fasta = background.Fasta
        reads = self.Files.copy()
        if self.pe:
            r1, r2 = [Path(f"{folder}/filtered_{r}.fq") for r in ["R1", "R2"]]
            bam2fastq = f"-1 {r1} -2 {r2} -s {folder}/filtered_singletons.fq"
            self.Files = {r1:ReadDirection.FORWARD, r2:ReadDirection.REVERSE}
        else:
            rs = Path(f"{folder}/filtered.fq")
            bam2fastq = f">{rs}"
            self.Files = {rs:ReadDirection.SINGLE}

        # "-f 4" means "get unmapped reads"
        # https://broadinstitute.github.io/picard/explain-flags.html
        cmd = f"""\
        {Executable.BWA} mem -t {params.threads} {fasta} {' '.join(str(r) for r in reads)} \
        | {Executable.SAMTOOLS} view -bS -f 4 -@ {params.threads} - \
        | {Executable.SAMTOOLS} sort -@ {params.threads} - \
        | {Executable.SAMTOOLS} fastq --verbosity 1 -N {bam2fastq} \
        """
        logging.info(f"Filtering reads that map to [{fasta.name}]")
        Run(cmd, params.workspace, f"filter--{StripExt(fasta.name)}.log")

    # trim reads by quality
    def Trim(self):
        params = self._params

        def _run_trimmomatic(outputs: list[str]):
            adapters_folder = f"{Path(sys.executable).parents[1]}/share/trimmomatic/adapters"
            adapters = f"ILLUMINACLIP:{adapters_folder}/TruSeq3-PE.fa:2:3:10"

            cmd = f"""\
            {Executable.TRIMMOMATIC} {'PE' if self.pe else 'SE'} -threads {params.threads} \
                {' '.join([str(r) for r in reads])} \
                {' '.join(outputs)} \
                {adapters} LEADING:3 TRAILING:3 SLIDINGWINDOW:4:15 MINLEN:36 \
            """
            logging.info(f"Quality trimming reads")
            Run(cmd, params.workspace, f"trim.log")

        outputs = []
        prefix = self.Folder.joinpath("trimmed")
        reads = self.Files.copy()
        if self.pe:
            paired = [f"{prefix}_R1.fq", f"{prefix}_R2.fq"]
            singles = [f"{prefix}_se.R1.fq", f"{prefix}_se.R2.fq"]
            _run_trimmomatic([paired[0], singles[0], paired[1], singles[1]])
            aggregate_singletons = f"{prefix}_singletons.fq"
            for spath in singles:
                Shell(f"cat {spath} >>{aggregate_singletons} && rm {spath}")
            self.Files = {Path(r):d for r, d in zip(paired, [ReadDirection.FORWARD, ReadDirection.REVERSE])}
            self.Files[Path(aggregate_singletons)] = ReadDirection.SINGLE
        else:
            outputs = [f"{prefix}.fq"]
            _run_trimmomatic(outputs)
            self.Files = {Path(r):ReadDirection.SINGLE for r in outputs}

    def Assemble(self):
        # megahit is optimal, outperforming spades in both time and quality
        # but from experience, spades contigs are not a strict subset of megahit's
        # so we leave spades here as an option
        # https://doi.org/10.1093/bib/bbad087

        # comparison of long read assemblers indicate flye is optimal
        # https://doi.org/10.12688%2Ff1000research.21782.4
        pass