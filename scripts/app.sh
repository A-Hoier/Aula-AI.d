#!/bin/bash
# This script is used to run the Dash application with Uvicorn.
 uv run uvicorn app:asgi_app --host 0.0.0.0 --port 8050 --workers 1