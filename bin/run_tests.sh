#!/bin/bash

# Check if a test file is provided as an argument
if [ -z "$1" ]; then
  pytest --verbose tests
else
  # Run the specified test file
  pytest --verbose "$1"
fi
