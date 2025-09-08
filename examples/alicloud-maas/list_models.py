#!/usr/bin/env python3
"""
List all available models from Alibaba Cloud DashScope API.
"""

import os
import sys
import json
import requests
from typing import Dict, List, Optional
import argparse

def load_api_key(config_path: str = "alicloud_config.toml") -> Optional[str]:
    """Load API key from config file or environment variable."""
    
    # First try environment variable
    api_key = os.environ.get("ALIBABA_CLOUD_API_KEY")
    if api_key:
        return api_key
    
    # Try loading from config file
    try:
        import tomli
        with open(config_path, "rb") as f:
            config = tomli.load(f)
            for provider in config.get("providers", []):
                if provider.get("api_base") and "dashscope.aliyuncs.com" in provider["api_base"]:
                    return provider.get("api_key")
    except ImportError:
        # If tomli is not installed, try basic parsing
        try:
            with open(config_path, "r") as f:
                for line in f:
                    if "api_key" in line and "=" in line:
                        # Extract value between quotes
                        parts = line.split("=", 1)[1].strip()
                        if parts.startswith('"') and parts.endswith('"'):
                            return parts[1:-1]
                        elif parts.startswith("'") and parts.endswith("'"):
                            return parts[1:-1]
        except FileNotFoundError:
            pass
    
    return None

def list_models(api_key: str, endpoint: str = "https://dashscope.aliyuncs.com/compatible-mode/v1") -> Dict:
    """List all available models from the API."""
    
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    try:
        response = requests.get(f"{endpoint}/models", headers=headers, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"❌ Error fetching models: {e}", file=sys.stderr)
        return None

def format_model_info(model: Dict) -> str:
    """Format model information for display."""
    model_id = model.get("id", "unknown")
    created = model.get("created", "")
    owned_by = model.get("owned_by", "")
    
    # Convert timestamp if it exists
    if created and isinstance(created, (int, float)):
        from datetime import datetime
        created_date = datetime.fromtimestamp(created).strftime("%Y-%m-%d")
    else:
        created_date = ""
    
    info = f"  • {model_id}"
    if owned_by:
        info += f" (by {owned_by})"
    if created_date:
        info += f" - Created: {created_date}"
    
    return info

def categorize_models(models: List[Dict]) -> Dict[str, List[Dict]]:
    """Categorize models by their prefix/type."""
    categories = {
        "qwen": [],
        "qwen-vl": [],
        "qwen-audio": [],
        "qwen-math": [],
        "qwen-coder": [],
        "qwen-plus": [],
        "qwen-turbo": [],
        "qwen-max": [],
        "qwen-long": [],
        "deepseek": [],
        "moonshot": [],
        "yi": [],
        "baichuan": [],
        "chatglm": [],
        "llama": [],
        "other": []
    }
    
    for model in models:
        model_id = model.get("id", "").lower()
        categorized = False
        
        # Check each category
        for category in categories.keys():
            if category != "other" and category in model_id:
                categories[category].append(model)
                categorized = True
                break
        
        if not categorized:
            categories["other"].append(model)
    
    # Remove empty categories
    return {k: v for k, v in categories.items() if v}

def main():
    parser = argparse.ArgumentParser(description="List available models from Alibaba Cloud DashScope")
    parser.add_argument("--api-key", help="API key (can also use ALIBABA_CLOUD_API_KEY env var)")
    parser.add_argument("--config", default="alicloud_config.toml", help="Path to config file")
    parser.add_argument("--endpoint", default="https://dashscope.aliyuncs.com/compatible-mode/v1", 
                       help="API endpoint")
    parser.add_argument("--json", action="store_true", help="Output raw JSON")
    parser.add_argument("--simple", action="store_true", help="Simple list of model IDs only")
    
    args = parser.parse_args()
    
    # Get API key
    api_key = args.api_key or load_api_key(args.config)
    if not api_key:
        print("❌ Error: No API key found!", file=sys.stderr)
        print("Please provide API key via:", file=sys.stderr)
        print("  1. --api-key argument", file=sys.stderr)
        print("  2. ALIBABA_CLOUD_API_KEY environment variable", file=sys.stderr)
        print("  3. alicloud_config.toml file", file=sys.stderr)
        sys.exit(1)
    
    # Fetch models
    print(f"🔍 Fetching models from {args.endpoint}...")
    result = list_models(api_key, args.endpoint)
    
    if not result:
        sys.exit(1)
    
    models = result.get("data", [])
    
    if not models:
        print("⚠️ No models found")
        return
    
    # Output based on format
    if args.json:
        print(json.dumps(result, indent=2))
    elif args.simple:
        for model in models:
            print(model.get("id", "unknown"))
    else:
        print(f"\n✅ Found {len(models)} available models\n")
        print("=" * 70)
        
        # Categorize and display
        categories = categorize_models(models)
        
        category_names = {
            "qwen": "🤖 Qwen Base Models",
            "qwen-turbo": "⚡ Qwen Turbo (Fast)",
            "qwen-plus": "➕ Qwen Plus (Enhanced)",
            "qwen-max": "💪 Qwen Max (Most Capable)",
            "qwen-long": "📜 Qwen Long Context",
            "qwen-vl": "👁️ Qwen Vision-Language",
            "qwen-audio": "🎵 Qwen Audio",
            "qwen-math": "🔢 Qwen Math",
            "qwen-coder": "💻 Qwen Coder",
            "deepseek": "🔍 DeepSeek Models",
            "moonshot": "🌙 Moonshot/Kimi Models",
            "yi": "🎯 Yi Models",
            "baichuan": "🐉 Baichuan Models",
            "chatglm": "💬 ChatGLM Models",
            "llama": "🦙 LLaMA Models",
            "other": "📦 Other Models"
        }
        
        for category, category_models in categories.items():
            if category_models:
                print(f"\n{category_names.get(category, category.title())}:")
                print("-" * 40)
                
                # Sort models by ID
                category_models.sort(key=lambda x: x.get("id", ""))
                
                for model in category_models:
                    print(format_model_info(model))
        
        print("\n" + "=" * 70)
        print(f"📊 Summary: {len(models)} total models available")
        
        # Show category counts
        print("\nModels by category:")
        for category, category_models in categories.items():
            if category_models:
                print(f"  • {category_names.get(category, category.title())}: {len(category_models)}")

if __name__ == "__main__":
    main()