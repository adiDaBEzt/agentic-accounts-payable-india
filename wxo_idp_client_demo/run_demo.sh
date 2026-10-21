#!/bin/bash
set -e

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
cd "$DIR"

echo "=========================================================="
echo "  IBM watsonx Orchestrate — Intelligent Document Processing"
echo "  Client Demo Application"
echo "=========================================================="

if [ ! -f .env ]; then
    if [ -f ../.env ]; then
        echo "Copying .env from parent directory..."
        cp ../.env .env
    else
        echo "Creating .env from .env.example..."
        cp .env.example .env
        echo "PLEASE NOTE: Edit .env with your IBM Cloud API Key before running."
    fi
fi

if [ ! -d ".venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv .venv
    .venv/bin/pip install --upgrade pip
    .venv/bin/pip install -r requirements.txt
fi

echo "Starting server on http://127.0.0.1:8000 ..."
.venv/bin/uvicorn app:app --host 127.0.0.1 --port 8000 --reload
