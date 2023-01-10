#!/bin/bash

# Change Poetry settings to better deal with working in a container
poetry config cache-dir $(pwd)/.cache
poetry config virtualenvs.in-project true
