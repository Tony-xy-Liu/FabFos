import setuptools

with open("./src/version.txt") as f:
    VER = f.readline()

with open("README.md", "r", encoding="utf-8") as f:
    long_description = f.read()

PKG_NAME = "fabfos"
PKG_DIR = PKG_NAME.replace('-', '_')

setuptools.setup(
    name="fabfos",
    version=VER,
    author="Tony Liu, Connor Morgan-Lang, Avery Noonan, Zach Armstrong and Steven J. Hallam",
    author_email="shallam@mail.ubc.ca",
    description="A toolkit for assembling and preprocessing fosmid pools",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/hallamlab/FabFos",
    project_urls={
        "Bug Tracker": "https://github.com/hallamlab/FabFos/issues",
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "Operating System :: Linux",
    ],
    package_dir={"": "src"},
    # packages=setuptools.find_packages(where="src"),
    packages=[PKG_DIR],
    # package_data={
    #     # "":["*.txt"],
    #     # "package-name": ["*.txt"],
    #     # "test_package": ["res/*.txt"],
    # },
    entry_points={
        'console_scripts': [
            f'fabfos = {PKG_NAME}:main',
        ]
    },
    python_requires=">=3.6",
)