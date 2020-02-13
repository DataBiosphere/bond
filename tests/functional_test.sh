#!/usr/bin/env bash

cp tests/config/config.ini config.ini

python -m unittest discover -s tests/integration -p "*_test.py"
