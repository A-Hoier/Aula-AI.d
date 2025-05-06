#!/bin/bash
# This script is used to run the FastAPI application with Uvicorn.
uv run uvicorn api:app --host 0.0.0.0 --port 8000 --workers 2 