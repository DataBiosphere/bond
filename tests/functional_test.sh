#!/usr/bin/env bash

cp tests/config/config.ini config.ini

python3 -m unittest discover -s tests/unit -p "*_test.py"
