#!/bin/bash
# Podcast Generator - Quick Launch Script
# This script helps launch all components in the correct order

set -e

echo "=========================================="
echo "Podcast Generator Launch Helper"
echo "=========================================="
echo ""

# Check if script file exists
SCRIPT_FILE="${1:-scripts/example_podcast.md}"
OUTPUT_FILE="${2:-output/podcast_output.wav}"

if [ ! -f "$SCRIPT_FILE" ]; then
    echo "❌ Error: Script file not found: $SCRIPT_FILE"
    echo ""
    echo "Usage: $0 [script.md] [output.wav]"
    echo "Example: $0 scripts/example_podcast.md output/my_podcast.wav"
    exit 1
fi

echo "📄 Script: $SCRIPT_FILE"
echo "🔊 Output: $OUTPUT_FILE"
echo ""

# Check if dataflow is already running
if dora list 2>/dev/null | grep -q "podcast-generator\|dataflow"; then
    echo "⚠️  Warning: A dataflow might already be running."
    echo "   Stopping it first..."
    dora stop 2>/dev/null || true
    sleep 2
fi

echo "=========================================="
echo "Launch Instructions:"
echo "=========================================="
echo ""
echo "You need to run these commands in SEPARATE terminals:"
echo ""
echo "Terminal 1 (Dataflow):"
echo "  cd $(pwd)"
echo "  dora start dataflow.yml"
echo ""
echo "Terminal 2 (Script Segmenter) - Launch IMMEDIATELY after Terminal 1:"
echo "  cd $(pwd)"
echo "  python script_segmenter.py --input-file $SCRIPT_FILE"
echo ""
echo "Terminal 3 (Voice Output) - Launch IMMEDIATELY after Terminal 2:"
echo "  cd $(pwd)"
echo "  python voice_output.py --output-file $OUTPUT_FILE"
echo ""
echo "Terminal 4 (Viewer - Optional):"
echo "  cd $(pwd)"
echo "  python viewer.py"
echo ""
echo "=========================================="
echo "⏰ TIMING IS CRITICAL!"
echo "=========================================="
echo "The dynamic nodes (Terminal 2 & 3) must connect within a few seconds"
echo "of the dataflow starting, otherwise the dataflow will quit."
echo ""
echo "Press Ctrl+C in any terminal to stop."
echo ""
