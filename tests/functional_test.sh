#!/usr/bin/env bash

cp tests/config/config.ini config.ini

python -m unittest discover -s tests/unit -p "*_test.py"
