#!/bin/bash
set -a
export PYTHONPATH=$PYTHONPATH:$(pwd)/app
# source .env
uvicorn --reload --log-level debug backend.main:app --host 0.0.0.0 --port 8003
