#!/bin/bash

# Direct Python test runner for Alibaba Cloud models
# Usage: ./run_direct_test.sh [model] [mode]
# Examples:
#   ./run_direct_test.sh                    # Interactive mode
#   ./run_direct_test.sh qwen-plus          # Test qwen-plus with quick mode
#   ./run_direct_test.sh deepseek-chat full # Test deepseek-chat with full questions

set -e

# Check if arguments provided, otherwise go interactive
if [ $# -eq 0 ]; then
    # Interactive mode
    echo "==========================================
🤖 Alibaba Cloud Model Test - Interactive
=========================================="
    
    echo "
📋 Available Models:
  1. qwen-turbo    - Fast & cost-effective
  2. qwen-plus     - Enhanced performance
  3. qwen-max      - Most capable
  4. deepseek-v3 - latest DeepSeek chat models
  5. deepseek-r1-0528 - latest DeepSeek reasoning models
  6. Moonshot-Kimi-K2-Instruct - Moonshot-Kimi-K2-Instruct
  7. glm-4.5 - glm-4.5

"
    
    echo -n "
👉 Select model (1-7) [default: 1]: "
    read model_choice
    
    case "${model_choice:-1}" in
        1) MODEL="qwen-turbo" ;;
        2) MODEL="qwen-plus" ;;
        3) MODEL="qwen-max" ;;
        4) MODEL="deepseek-v3" ;;
        5) MODEL="deepseek-r1-0528" ;;
        6) MODEL="Moonshot-Kimi-K2-Instruct" ;;
        *) MODEL="qwen-max" ;;
    esac
    
    echo "✅ Selected: $MODEL"
    
    echo "
📝 Test Modes:
  1. quick  - 3 test questions
  2. full   - 10 test questions
  3. custom - Select specific questions"
    
    echo -n "
👉 Select mode (1-3) [default: 1]: "
    read mode_choice
    
    case "${mode_choice:-1}" in
        1) MODE="quick" ;;
        2) MODE="full" ;;
        3) 
            MODE="custom"
            echo "
📌 Test Questions:
  1. What is artificial intelligence and how does it work?
  2. Write a Python function to calculate fibonacci numbers.
  3. Explain quantum computing in simple terms.
  4. 请用中文介绍一下机器学习的主要应用。
  5. Compare cloud computing vs on-premise solutions.
  6. Write a haiku about artificial intelligence.
  7. What are the ethical considerations of AI?
  8. Implement a binary search algorithm in Python.
  9. 解释深度学习和传统机器学习的区别。
  10. What are best practices for prompt engineering?"
            
            echo -n "
👉 Select questions (comma-separated, e.g., 1,3,5 or 'all'): "
            read questions
            
            if [ "$questions" = "all" ]; then
                CUSTOM_QUESTIONS="What is artificial intelligence and how does it work?|Write a Python function to calculate fibonacci numbers.|Explain quantum computing in simple terms.|请用中文介绍一下机器学习的主要应用。|Compare cloud computing vs on-premise solutions.|Write a haiku about artificial intelligence.|What are the ethical considerations of AI?|Implement a binary search algorithm in Python.|解释深度学习和传统机器学习的区别。|What are best practices for prompt engineering?"
            else
                # Build custom questions based on selection
                CUSTOM_QUESTIONS=""
                IFS=',' read -ra INDICES <<< "$questions"
                for i in "${INDICES[@]}"; do
                    case "$(echo $i | tr -d ' ')" in
                        1) Q="What is artificial intelligence and how does it work?" ;;
                        2) Q="Write a Python function to calculate fibonacci numbers." ;;
                        3) Q="Explain quantum computing in simple terms." ;;
                        4) Q="请用中文介绍一下机器学习的主要应用。" ;;
                        5) Q="Compare cloud computing vs on-premise solutions." ;;
                        6) Q="Write a haiku about artificial intelligence." ;;
                        7) Q="What are the ethical considerations of AI?" ;;
                        8) Q="Implement a binary search algorithm in Python." ;;
                        9) Q="解释深度学习和传统机器学习的区别。" ;;
                        10) Q="What are best practices for prompt engineering?" ;;
                        *) continue ;;
                    esac
                    if [ -z "$CUSTOM_QUESTIONS" ]; then
                        CUSTOM_QUESTIONS="$Q"
                    else
                        CUSTOM_QUESTIONS="$CUSTOM_QUESTIONS|$Q"
                    fi
                done
                
                if [ -z "$CUSTOM_QUESTIONS" ]; then
                    echo "❌ No valid questions selected, using quick mode"
                    MODE="quick"
                fi
            fi
            ;;
        *) MODE="quick" ;;
    esac
    
    echo "✅ Selected mode: $MODE"
else
    # Command-line arguments provided
    MODEL="${1:-qwen-turbo}"
    MODE="${2:-quick}"
fi

echo "=========================================="
echo "🚀 Alibaba Cloud Direct Test Runner"
echo "=========================================="
echo "Model: $MODEL"
echo "Mode: $MODE"
echo "=========================================="
echo ""

# Check for API key
if [ -z "$ALIBABA_CLOUD_API_KEY" ]; then
    echo "⚠️  Warning: ALIBABA_CLOUD_API_KEY environment variable not set"
    echo "   Set it with: export ALIBABA_CLOUD_API_KEY='sk-your-key-here'"
    echo ""
    echo -n "Enter your API key now (or press Enter to continue without): "
    read api_key
    if [ ! -z "$api_key" ]; then
        export ALIBABA_CLOUD_API_KEY="$api_key"
        echo "✅ API key set for this session"
    fi
    echo ""
fi

# Export environment variables for the Python script
export TEST_MODEL="$MODEL"
export TEST_MODE="$MODE"
if [ ! -z "$CUSTOM_QUESTIONS" ]; then
    export CUSTOM_QUESTIONS="$CUSTOM_QUESTIONS"
fi

# Check if Dora is running
echo "📋 Checking Dora status..."
if ! dora check > /dev/null 2>&1; then
    echo "❌ Dora is not running. Please start it with: dora up"
    exit 1
fi
echo "✅ Dora is running"
echo ""

# Check if maas dataflow is already running
MAAS_DATAFLOW="alicloud-maas-standalone"
if dora list | grep -q "$MAAS_DATAFLOW.*Running"; then
    echo "✅ MaaS dataflow is already running"
else
    echo "🚀 Starting MaaS dataflow..."
    
    # Stop any existing dataflow with the same name
    dora stop --name "$MAAS_DATAFLOW" 2>/dev/null || true
    sleep 1
    
    # Create standalone maas dataflow
    cat > standalone_maas.yml << 'EOF'
nodes:
  # MaaS Client - Standalone node for direct Python testing
  - id: maas-client
    build: cargo build -p dora-maas-client --release
    path: ../../target/release/dora-maas-client
    inputs:
      text: test-client/text
    outputs:
      - text
      - status
      - log
    env:
      MAAS_CONFIG_PATH: alicloud_config.toml
      LOG_LEVEL: INFO
      RUST_LOG: info

  # Dynamic test client placeholder
  - id: test-client
    path: dynamic
    outputs:
      - text
    inputs:
      text: maas-client/text
      status: maas-client/status
EOF
    
    # Start the dataflow in detached mode
    dora start standalone_maas.yml --name "$MAAS_DATAFLOW" --detach
    echo "⏳ Waiting for dataflow to be ready..."
    sleep 3
    echo "✅ MaaS dataflow started"
fi

echo ""
echo "🐍 Running Python test script..."
echo "=========================================="

# Run the Python test script with environment variables set
# The Python script reads TEST_MODEL and TEST_MODE from environment
python test_alicloud_models.py

echo ""
echo "=========================================="
echo "✅ Test completed!"
echo ""
echo "Note: MaaS dataflow is still running. To stop it:"
echo "  dora stop --name $MAAS_DATAFLOW"
echo ""