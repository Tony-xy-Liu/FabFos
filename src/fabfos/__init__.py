import os, sys
import argparse
from pathlib import Path


class ArgumentParser(argparse.ArgumentParser):
    def error(self, message):
        self.print_help(sys.stderr)
        self.exit(2, '\n%s: error: %s\n' % (self.prog, message))

def main():
    parser = ArgumentParser(
        prog = 'Fosmid Walk',
        description = "v1.0",
        # epilog = 'Text at the bottom of help',
    )