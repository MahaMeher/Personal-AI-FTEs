#!/bin/bash
# AI Employee - Bronze Tier Startup Script
# This script starts both the Filesystem Watcher and Orchestrator

echo "============================================"
echo "  AI Employee v0.1 - Bronze Tier"
echo "============================================"
echo ""

cd "$(dirname "$0")"

echo "Starting Filesystem Watcher (background)..."
python scripts/filesystem_watcher.py &
WATCHER_PID=$!

sleep 2

echo "Starting Orchestrator (background)..."
python scripts/orchestrator.py &
ORCHESTRATOR_PID=$!

echo ""
echo "============================================"
echo "  Both services started!"
echo ""
echo "  Watcher PID: $WATCHER_PID"
echo "  Orchestrator PID: $ORCHESTRATOR_PID"
echo ""
echo "  To stop: Press Ctrl+C or run:"
echo "    kill $WATCHER_PID $ORCHESTRATOR_PID"
echo ""
echo "  To test: Drop a file in the Inbox folder"
echo "============================================"

# Wait for both processes
wait
