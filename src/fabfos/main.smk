import os
from pathlib import Path
import json
from fabfos.models import ReadsManifest, BackgroundGenome, Assembly, EndSequences
from fabfos.models import RawContigs, Scaffolds, LenFilteredContigs
from fabfos.models import QCStatsForAssemblies

# the actual commands to call each tool are found in src/fabfos/steps/*.py

SRC = Path(config["src"])
LOGS = Path(config["log"])
THREADS = int(config["threads"])

params_path = Path("params.json")
if params_path.exists():
    with open(params_path) as j:
        params = json.load(j)
else:
    params = {}

assembly_params = Assembly.Load(Assembly.ARG_FILE)
reads = ReadsManifest.Load(ReadsManifest.ARG_FILE)
endseqs = EndSequences.Load(EndSequences.ARG_FILE)
no_trim = params.get("no_trim", False)

# -------------------------------------
# snakemake

targets = [
    f"{Scaffolds.MANIFEST if endseqs.given else LenFilteredContigs.MANIFEST}"
]
if len(assembly_params.modes)>0:
    targets.append(f"{QCStatsForAssemblies.STATS_FILE}")
rule target:
    input: expand("{t}", t=targets)

rule standardize_reads:
    input: f"{ReadsManifest.ARG_FILE}"
    output: f"{ReadsManifest.STD}"
    params:
        src=SRC
    threads: THREADS
    shell:
        """\
        PYTHONPATH={params.src}:$PYTHONPATH
        python -m fabfos api --step standardize_reads --args {threads} {output} {input}
        """

rule quality_trim:
    input: f"{ReadsManifest.STD}"
    output: f"{ReadsManifest.TRIM}"
    params:
        src=SRC,
    threads: THREADS
    shell:
        """\
        PYTHONPATH={params.src}:$PYTHONPATH
        python -m fabfos api --step quality_trim --args {threads} {output} {input}
        """

rule filter_background:
    input:
        f"{ReadsManifest.STD if no_trim else ReadsManifest.TRIM}",
        f"{BackgroundGenome.ARG_FILE}"
    output: f"{ReadsManifest.FILTER}"
    params:
        src=SRC,
    threads: THREADS
    shell:
        """\
        PYTHONPATH={params.src}:$PYTHONPATH
        python -m fabfos api --step background_filter --args {threads} {output} {input}
        """

if len([r for g in reads.AllReads() for r in g]) > 0:
    if params.get("background") is None:
        if no_trim:
            reads_input = ReadsManifest.ARG_FILE
        else:
            reads_input = ReadsManifest.TRIM
    else:
        reads_input = ReadsManifest.FILTER
else:
    reads_input = ReadsManifest.ARG_FILE

rule acquire_contigs:
    input:
        f"{reads_input}",
        f"{Assembly.ARG_FILE}"
    output: f"{RawContigs.MANIFEST}"
    params:
        src=SRC,
    threads: THREADS
    shell:
        """\
        PYTHONPATH={params.src}:$PYTHONPATH
        python -m fabfos api --step assembly --args {threads} {output} {input}
        """

rule scaffold:
    input:
        f"{RawContigs.MANIFEST}",
        f"{EndSequences.ARG_FILE}"
    output: f"{Scaffolds.MANIFEST}"
    params:
        src=SRC,
    threads: THREADS
    shell:
        """\
        PYTHONPATH={params.src}:$PYTHONPATH
        python -m fabfos api --step scaffold --args {threads} {output} {input}
        """

rule filter_contigs_by_length:
    input: f"{RawContigs.MANIFEST}"
    output: f"{LenFilteredContigs.MANIFEST}"
    params:
        src=SRC,
    threads: THREADS
    shell:
        """\
        PYTHONPATH={params.src}:$PYTHONPATH
        python -m fabfos api --step filter_contigs_by_length --args {threads} {output} {input}
        """

qc_assemblies_input = [reads_input, RawContigs.MANIFEST, Assembly.ARG_FILE]
if endseqs.given:
    qc_assemblies_input+=[Scaffolds.MANIFEST]
    contig_type = "scaffolds"
else:
    qc_assemblies_input+=[LenFilteredContigs.MANIFEST]
    contig_type = "contigs"

rule qc_assemblies:
    input: expand("{f}", f=qc_assemblies_input)
    output: f"{QCStatsForAssemblies.STATS_FILE}"
    params:
        src=SRC,
        contig_type=contig_type
    threads: THREADS
    shell:
        """\
        PYTHONPATH={params.src}:$PYTHONPATH
        python -m fabfos api --step qc_assemblies --args {threads} {output} {input} {params.contig_type}
        """
