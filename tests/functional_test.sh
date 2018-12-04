#!/usr/bin/env bash

cp tests/config/config.ini config.ini

python tests/test_runner.py /google-cloud-sdk --test-path=tests/integration
