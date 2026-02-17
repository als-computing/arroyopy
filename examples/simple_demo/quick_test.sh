#!/bin/bash
#
# Quick test script for the simple demo
# This runs all three components sequentially for testing
#

set -e

echo "=================================="
echo "Arroyopy Simple Demo - Quick Test"
echo "=================================="
echo ""
echo "This will:"
echo "1. Start the pipeline in the background"
echo "2. Start the sink in the background"
echo "3. Send 5 test messages"
echo "4. Clean up"
echo ""
echo "Press Ctrl+C at any time to stop"
echo ""

# Change to the script's directory
cd "$(dirname "$0")"

# Cleanup function
cleanup() {
    echo ""
    echo "Cleaning up..."
    if [ ! -z "$SINK_PID" ]; then
        kill $SINK_PID 2>/dev/null || true
    fi
    if [ ! -z "$PIPELINE_PID" ]; then
        kill $PIPELINE_PID 2>/dev/null || true
    fi
    wait 2>/dev/null || true
    echo "Done"
}

trap cleanup EXIT INT TERM

# Start the sink in background
echo "Starting sink..."
python sink.py > /tmp/arroyopy_sink.log 2>&1 &
SINK_PID=$!
sleep 1

# Start the pipeline in background
echo "Starting pipeline..."
arroyo-run run pipeline.yaml > /tmp/arroyopy_pipeline.log 2>&1 &
PIPELINE_PID=$!
sleep 2

# Send test messages
echo "Sending 5 test messages..."
echo ""
python source.py --count 5 --interval 0.5

echo ""
echo "Waiting for messages to propagate..."
sleep 2

echo ""
echo "=== Sink Output ==="
tail -20 /tmp/arroyopy_sink.log | grep -A 999 "Waiting for messages"
echo ""

echo "Test complete!"
echo ""
echo "Logs are in:"
echo "  /tmp/arroyopy_sink.log"
echo "  /tmp/arroyopy_pipeline.log"
