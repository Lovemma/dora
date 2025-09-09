# Alibaba Cloud MaaS Integration Example

This example demonstrates how to integrate Alibaba Cloud AI models with the Dora MaaS (Model-as-a-Service) client. Alibaba Cloud provides OpenAI-compatible APIs for various AI models including Qwen, DeepSeek, Moonshot (Kimi), and more.

## Overview

Alibaba Cloud's DashScope platform offers a wide range of AI models through an OpenAI-compatible API endpoint. This example shows how to:
- Configure the MaaS client to use Alibaba Cloud models
- Send questions to different models (Qwen, DeepSeek, Moonshot, etc.)
- Receive and display model responses
- Switch between different models dynamically

## Available Models

This example is configured to use several popular models available on Alibaba Cloud:

### Qwen Series (Alibaba's own models)
- **qwen-turbo**: Fast, cost-effective model for general tasks
- **qwen-plus**: Enhanced model with better performance
- **qwen-max**: Most capable Qwen model

### DeepSeek Models
- **deepseek-chat**: General conversation model
- **deepseek-coder**: Specialized for code generation

### Moonshot (Kimi) Models
- **moonshot-v1-8k**: 8K context window
- **moonshot-v1-32k**: 32K context window  
- **moonshot-v1-128k**: 128K context window

### Other Models
- **yi-34b-chat**: Yi series large language model
- **baichuan2-turbo**: Baichuan series model

## Prerequisites

1. **Alibaba Cloud Account**: You need an Alibaba Cloud account with DashScope API access
2. **API Key**: The example includes a test API key, but you should use your own for production
3. **Dora Framework**: Ensure Dora is installed and configured
4. **Rust & Python**: Both are required for running the nodes

## Setup

### Step 1: Build the MaaS Client

Navigate to the example directory and build the MaaS client with Alibaba Cloud support:

```bash
cd examples/alicloud-maas
cargo build -p dora-maas-client --release
```

### Step 2: Configure Your API Key

**Method 1: Environment Variable (Recommended)**

Set your API key as an environment variable:

```bash
export ALIBABA_CLOUD_API_KEY="sk-your-api-key-here"
export MAAS_CONFIG_PAT="maas_mcp_browser_config.toml"
```

**Method 2: Configuration File**

If you prefer to hardcode the API key (not recommended for production), edit `alicloud_config.toml`:

```toml
[[providers]]
id = "alicloud"
kind = "alicloud"
api_url = "https://dashscope.aliyuncs.com/compatible-mode/v1"
api_key = "sk-your-api-key-here"  # Replace with your actual API key
```

### Step 3: Start Dora Coordinator

Make sure the Dora coordinator is running:

```bash
dora up
```

## Running the Example

### Basic Demo

Run the demo that sends test questions to various Alibaba Cloud models:

```bash
dora start alicloud_demo.yml
```

This will:
1. Start the test questions generator node
2. Launch the MaaS client configured for Alibaba Cloud
3. Display responses from different models
4. Show both English and Chinese language capabilities

### What Happens

The demo will send 10 predefined test questions to different Alibaba Cloud models:
1. Questions about Alibaba Cloud and AI services (qwen-turbo)
2. Fibonacci sequence code generation (qwen-plus)
3. Quantum computing explanation (deepseek-chat)
4. Cloud API advantages/disadvantages (moonshot-v1-8k)
5. Chinese: AI model services introduction (qwen-turbo)
6. REST API authentication code (deepseek-coder)
7. Machine learning comparison (qwen-max)
8. AI ethics in healthcare (moonshot-v1-32k)
9. Chinese: Large language model explanation (qwen-plus)
10. Prompt engineering best practices (qwen-turbo)

Each response will be displayed in the terminal with the model name and question ID, demonstrating the variety and capabilities of Alibaba Cloud's AI offerings.

## Configuration Details

### Provider Configuration

The `alicloud_config.toml` file configures the Alibaba Cloud provider:

```toml
[[providers]]
id = "alicloud"
kind = "alicloud"
api_url = "https://dashscope.aliyuncs.com/compatible-mode/v1"
api_key = "sk-..."
proxy = false
```

### Model Routing

Each model is configured with routing information:

```toml
[[models]]
id = "qwen-turbo"
route = { provider = "alicloud", model = "qwen-turbo" }
```

This tells the MaaS client to route requests for "qwen-turbo" to the Alibaba Cloud provider.

## Customization

### Adding New Models

To add a new model available on Alibaba Cloud, add it to `alicloud_config.toml`:

```toml
[[models]]
id = "new-model-name"
route = { provider = "alicloud", model = "actual-model-id" }
```

### Modifying Test Questions

Edit `test_questions.py` to add your own test questions:

```python
TEST_QUESTIONS = [
    {
        "model": "qwen-turbo",
        "question": "Your custom question here",
    },
    # Add more questions...
]
```

### Changing System Prompt

Modify the system prompt in `alicloud_config.toml`:

```toml
system_prompt = "Your custom system prompt here"
```

## API Compatibility

Alibaba Cloud's DashScope API is compatible with OpenAI's Chat Completion API format. This means:
- Same request/response structure
- Compatible streaming support
- Similar error handling
- Familiar SDK usage patterns

## Cost Considerations

Different models have different pricing:
- **qwen-turbo**: Most cost-effective
- **qwen-plus**: Balanced price/performance
- **qwen-max**: Premium pricing for best quality
- **moonshot-v1-128k**: Higher cost for long context

Check Alibaba Cloud's pricing page for current rates.

## Troubleshooting

### API Key Issues
- Ensure your API key is valid and has appropriate permissions
- Check if your account has access to the models you're trying to use

### Connection Errors
- Verify the API endpoint URL is correct
- Check your internet connection
- Ensure no firewall is blocking the connection

### Model Not Found
- Verify the model name is correct
- Check if the model is available in your region
- Ensure your account has access to the specific model

### Response Errors
- Check the logs from the MaaS client for detailed error messages
- Verify the request format matches the API requirements
- Ensure you're not exceeding rate limits

## Advanced Usage

### Streaming Responses

The configuration enables streaming by default:

```toml
enable_streaming = true
```

This allows for real-time token generation display.

### Session Management

Each question is sent with a session ID for conversation context:

```python
node.send_output(
    "text",
    pa.array([question]),
    {"model": model, "session_id": f"test_session_{i}"}
)
```

### Multi-turn Conversations

The MaaS client maintains conversation history up to the configured limit:

```toml
max_history_exchanges = 10
```

## Resources

- [Alibaba Cloud DashScope Documentation](https://www.alibabacloud.com/help/en/model-studio/)
- [OpenAI Compatibility Guide](https://www.alibabacloud.com/help/en/model-studio/compatibility-of-openai-with-dashscope)
- [Model List and Capabilities](https://help.aliyun.com/document_detail/2712195.html)
- [API Reference](https://help.aliyun.com/document_detail/2712581.html)

## License

This example is part of the Dora project and follows the same licensing terms.