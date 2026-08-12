#!/usr/bin/env python3
import argparse
from pathlib import Path

parser = argparse.ArgumentParser()
parser.add_argument("output")
parser.add_argument("inputs", nargs="+")
args = parser.parse_args()
with Path(args.output).open("w") as target:
    for name in args.inputs:
        with Path(name).open() as source:
            for line in source:
                target.write(line)
