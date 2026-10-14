#!/bin/bash

set -e

# 1. Get the absolute path to the directory where THIS script is located
SCRIPT_DIR=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" &> /dev/null && pwd)

# Create collection
curl -X 'POST' \
  'http://localhost:8082/collections' \
  -H 'accept: application/json' \
  -H 'Content-Type: application/json' \
  -d @"$SCRIPT_DIR/data/collection.json"

# Add an item
curl -X 'POST' \
  'http://localhost:8082/collections/auth-test/items' \
  -H 'accept: application/json' \
  -H 'Content-Type: application/json' \
  -d @"$SCRIPT_DIR/data/item.json"
