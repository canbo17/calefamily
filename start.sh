#!/usr/bin/env bash
set -e

# 1) Install any new Python deps
pip install -r requirements.txt

# 2) Launch your app
exec python app.py
