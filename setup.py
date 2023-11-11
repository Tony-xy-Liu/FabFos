import os, sys
from pathlib import Path
HERE = Path(os.path.realpath(__file__)).parent
sys.path = [str(p) for p in set([
    HERE.joinpath("src")
]+sys.path)]
import setuptools
from fabfos.utils import USER, NAME, ENTRY_POINTS, VERSION

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

if __name__ == "__main__":
    setuptools.setup(
        name=NAME,
        version=VERSION,
        author="Tony Liu, Connor Morgan-Lang, Avery Noonan, Zach Armstrong, and Steven J. Hallam",
        author_email="shallam@mail.ubc.ca",
        description="Analysis pipeline for pooled fosmids",
        long_description=long_description,
        long_description_content_type="text/markdown",
        license_files = ('LICENSE',),
        url=f"https://github.com/{USER}/{NAME}",
        project_urls={
            "Bug Tracker": f"https://github.com/{USER}/{NAME}/issues",
        },
        classifiers=[
            "Programming Language :: Python :: 3",
            "Operating System :: OS Independent",
        ],
        package_dir={"": "src"},
        packages=setuptools.find_packages(where="src"),
        # packages=pks,
        package_data={
            "":[ # "" is all packages
                "version.txt",
                "deinterleave_fastq.sh",
            ],
            # examples
            # "package-name": ["*.txt"],
            # "test_package": ["res/*.txt"],
        },
        entry_points={
            'console_scripts': [f"{e} = {NAME}.cli:main" for e in ENTRY_POINTS],
        },
        python_requires=">=3.11",
        install_requires=[
            "packaging >=21.0",
        ]
    )