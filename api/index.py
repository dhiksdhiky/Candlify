"""
v2/api/index.py — Vercel Serverless Function Entrypoint
Exposes `app` for Vercel Python Runtime.
"""
import os
import sys

# Ensure v2 base directory is on path
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from server import app
