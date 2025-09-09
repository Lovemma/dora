# MCP Pass-Through Mode for MaaS Client

## Overview

The MaaS client now supports two modes for handling MCP (Model Context Protocol) tools:

1. **Local MCP Mode** (default): MaaS client hosts its own MCP servers and executes tools locally
2. **Pass-Through Mode**: MaaS client passes tool definitions and calls between the client and LLM

## Configuration

The mode is controlled by the `enable_local_mcp` flag in the configuration:

```toml
# Enable tools functionality
enable_tools = true

# Control MCP hosting mode
enable_local_mcp = false  # false = pass-through mode, true = local hosting
```

## Pass-Through Mode Behavior

When `enable_local_mcp = false`:

1. **Tool Definitions**: Client provides tool definitions via metadata parameter `tools` (JSON array)
2. **Tool Calls**: When LLM calls tools, MaaS client sends them back via `tool_calls` output
3. **Tool Results**: Client executes tools and sends results back via `tool_results` input
4. **Final Response**: MaaS client forwards results to LLM and returns the final response

## Data Flow

### Pass-Through Mode
```
Client → (tools in metadata) → MaaS Client → LLM
LLM → (tool calls) → MaaS Client → (tool_calls output) → Client
Client → (executes tools) → (tool_results input) → MaaS Client → LLM
LLM → (final response) → MaaS Client → Client
```

### Local MCP Mode (Original)
```
Client → MaaS Client → LLM
LLM → (tool calls) → MaaS Client (executes locally) → LLM
LLM → (final response) → MaaS Client → Client
```

## Input/Output Format

### Tool Definitions (in metadata)
```json
{
  "tools": "[{\"type\":\"function\",\"function\":{\"name\":\"get_weather\",\"description\":\"Get weather\",\"parameters\":{...}}}]"
}
```

### Tool Calls (output)
```json
[{
  "id": "call_abc123",
  "type": "function",
  "function": {
    "name": "get_weather",
    "arguments": "{\"location\":\"San Francisco\"}"
  }
}]
```

### Tool Results (input)
```json
[
  ["call_abc123", "The weather in San Francisco is sunny, 72°F"]
]
```

## Configuration Examples

### Pass-Through Mode
```toml
# maas_config_passthrough.toml
enable_tools = true
enable_local_mcp = false  # Pass-through mode
# No MCP server configuration needed
```

### Local MCP Mode
```toml
# maas_config_local_mcp.toml
enable_tools = true
enable_local_mcp = true  # Local hosting mode

[mcp]
[[mcp.servers]]
name = "filesystem"
protocol = "stdio"
command = "npx"
args = ["-y", "@modelcontextprotocol/server-filesystem", "/tmp"]
```

## Use Cases

### Pass-Through Mode is Ideal For:
- Moly client with its own MCP implementation
- Clients that need control over tool execution
- Security-sensitive environments where tools must run client-side
- Complex tool orchestration managed by the client

### Local MCP Mode is Ideal For:
- Simple clients without MCP support
- Server-side tool execution for better performance
- Centralized tool management
- Legacy compatibility

## Testing

```bash
# Test pass-through mode
export MAAS_CONFIG_PATH=maas_config_passthrough.toml
cargo run -p dora-maas-client

# Test local MCP mode
export MAAS_CONFIG_PATH=maas_config_local_mcp.toml
cargo run -p dora-maas-client
```

## Implementation Details

The implementation modifies three key areas:

1. **Configuration** (`src/config.rs`):
   - Added `enable_local_mcp` flag
   - Modified `init_tool_set()` to respect the flag

2. **Tool Handling** (`src/main.rs`):
   - Pass-through tool definitions from client metadata when `enable_local_mcp = false`
   - Send tool calls to client instead of executing locally
   - Accept tool results from client and forward to LLM

3. **New I/O Channels**:
   - Output: `tool_calls` - Sends tool call requests to client
   - Input: `tool_results` - Receives tool execution results from client

This design maintains backward compatibility while enabling flexible MCP handling for advanced clients like Moly.