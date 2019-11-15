#!/usr/bin/env bash
set -e

source .venv/bin/activate

# uncomment line below to enforce Python formating
#pylint .

#python3 -m unittest discover
python -m xmlrunner discover -o test-results/
