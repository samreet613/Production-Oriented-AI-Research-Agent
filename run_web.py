"""Launcher script for the Web UI dashboard."""

import sys
from src.web.app import start_server

if __name__ == "__main__":
    print("\n=======================================================")
    print("🚀 Starting Production AI Research Agent Web Dashboard")
    print("🌐 Open in browser: http://127.0.0.1:5000")
    print("=======================================================\n")
    start_server(host="127.0.0.1", port=5000, debug=False)
