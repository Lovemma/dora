#!/usr/bin/env python3
"""
Podcast Generator Viewer - Monitor all node logs and events
"""
import json
import sys
from datetime import datetime
import pyarrow as pa
from dora import Node


class Colors:
    """ANSI color codes for terminal output"""
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'


def format_timestamp(ts=None):
    """Format timestamp for display"""
    if ts:
        return datetime.fromtimestamp(ts).strftime("%H:%M:%S.%f")[:-3]
    return datetime.now().strftime("%H:%M:%S.%f")[:-3]


def get_node_icon(node_name):
    """Get emoji icon for each node"""
    icons = {
        "script-segmenter": "📝",
        "primespeech-daniu": "🎤",
        "primespeech-yifan": "🎙️",
        "voice-output": "🔊"
    }
    return icons.get(node_name, "📦")


def get_level_color(level):
    """Get color for log level"""
    colors = {
        "ERROR": Colors.RED,
        "WARNING": Colors.YELLOW,
        "INFO": Colors.CYAN,
        "DEBUG": Colors.GREEN
    }
    return colors.get(level, Colors.ENDC)


def print_log(log_data):
    """Print formatted log message"""
    try:
        if isinstance(log_data, str):
            data = json.loads(log_data)
        else:
            data = log_data

        node_name = data.get("node", "unknown")
        level = data.get("level", "INFO")
        message = data.get("message", "")
        timestamp = data.get("timestamp", None)

        icon = get_node_icon(node_name)
        color = get_level_color(level)
        ts_str = format_timestamp(timestamp)

        print(f"{Colors.BOLD}[{ts_str}]{Colors.ENDC} {icon} {color}{node_name.upper()}: {message}{Colors.ENDC}")

    except Exception as e:
        print(f"{Colors.RED}[Viewer] Failed to parse log: {e}{Colors.ENDC}")


def main():
    """Main viewer loop"""
    node = Node("viewer")

    print("\n" + "="*70)
    print(f"{Colors.BOLD}🎙️ Podcast Generator Viewer{Colors.ENDC}")
    print("="*70)
    print("Monitoring pipeline events...\n")

    for event in node:
        if event["type"] == "INPUT":
            input_id = event["id"]

            try:
                # All log inputs
                if input_id.endswith("_log"):
                    log_data = event["value"][0].as_py()
                    print_log(log_data)

                # Text segments being sent to TTS
                elif input_id == "daniu_text":
                    text = event["value"][0].as_py()
                    print(f"{Colors.BOLD}[{format_timestamp()}]{Colors.ENDC} 🎤 {Colors.GREEN}大牛: {text}{Colors.ENDC}")

                elif input_id == "yifan_text":
                    text = event["value"][0].as_py()
                    print(f"{Colors.BOLD}[{format_timestamp()}]{Colors.ENDC} 🎙️ {Colors.GREEN}一帆: {text}{Colors.ENDC}")

                # Script completion
                elif input_id == "script_complete":
                    print(f"\n{Colors.BOLD}[{format_timestamp()}]{Colors.ENDC} {Colors.GREEN}✅ PODCAST GENERATION COMPLETE!{Colors.ENDC}\n")

            except Exception as e:
                print(f"{Colors.RED}[Viewer] Error processing event: {e}{Colors.ENDC}")

        elif event["type"] == "STOP":
            break


if __name__ == "__main__":
    main()
