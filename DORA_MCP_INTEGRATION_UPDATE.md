# IMPORTANT UPDATE: Dora HAS MCP Support!

## Critical Finding
**Dora DOES have MCP (Model Context Protocol) support** through the `dora-maas-client` component. This was not visible in `dora-openai-websocket` but exists as a separate module.

## Dora's MCP Implementation Location
- **Path**: `/node-hub/dora-maas-client/`
- **Dependency**: `rmcp = { version = "0.3.2" }` (same SDK as Moly!)
- **Status**: Fully functional with recent fixes

## Dora's MCP Architecture

### 1. Tool Management (`src/tool.rs`)
```rust
// Dora uses the same rmcp SDK as Moly
use rmcp::{
    RoleClient,
    model::{CallToolRequestParam, CallToolResult, Tool as McpTool},
    service::{RunningService, ServerSink},
};

// Tool adapter pattern similar to Moly
pub struct McpToolAdapter {
    tool: McpTool,
    server: ServerSink,
}

// Tool set management
pub struct ToolSet {
    tools: HashMap<String, Arc<dyn Tool>>,
    clients: HashMap<String, RunningService<RoleClient, ()>>,
}
```

### 2. MCP Server Support (`src/config.rs`)
Dora supports multiple MCP transport types:
- **HTTP**: Web-based MCP servers
- **SSE**: Server-Sent Events
- **Stdio**: Child process communication (fixed in recent update)

```rust
pub enum McpServerTransportConfig {
    Http { url: String },
    Sse { url: String },
    Stdio {
        command: String,
        args: Vec<String>,
        envs: HashMap<String, String>,
    },
}
```

### 3. Recent MCP Fixes (from MCP_TOOL_FIXES.md)
Dora recently fixed several MCP issues:
1. **Stdio pipe configuration** - Changed from `inherit()` to `piped()` for proper IPC
2. **Graceful server initialization** - Continue if one server fails
3. **Tool call accumulation** - Properly handle streaming tool calls
4. **Automatic response continuation** - Execute tools and get final response
5. **Session management** - Added methods for tool messages

## Updated Comparison: Dora vs Moly MCP Support

| Feature | Dora (maas-client) | Moly | Gap |
|---------|-------------------|------|-----|
| **MCP SDK** | ✅ rmcp 0.3.2 | ✅ rmcp 0.2.0 | None (Dora newer) |
| **Transport Support** | | | |
| - HTTP | ✅ Yes | ✅ Yes | None |
| - SSE | ✅ Yes | ✅ Yes | None |
| - Stdio | ✅ Yes (fixed) | ✅ Yes | None |
| **Tool Management** | | | |
| - Tool discovery | ✅ Yes | ✅ Yes | None |
| - Tool execution | ✅ Yes | ✅ Yes | None |
| - Tool adapter pattern | ✅ Yes | ✅ Yes | None |
| - Error handling | ✅ Graceful | ✅ Yes | None |
| **Architecture Differences** | | | |
| - Tool namespacing | ❌ No | ✅ server_id__tool | Major |
| - Tool registry | ✅ HashMap | ✅ ToolRegistry | Minor |
| - Tool approval UI | ❌ No | ✅ Interactive | Major |
| - Integration point | maas-client | realtime widget | Different |

## Key Architectural Differences

### 1. Integration Point
- **Dora**: MCP in `dora-maas-client` (OpenAI Chat API node)
- **Moly**: MCP in OpenAI Realtime API implementation

### 2. Tool Namespacing
- **Dora**: Direct tool names (no namespace)
- **Moly**: Namespaced `server_id__tool_name` format

### 3. User Approval
- **Dora**: Automatic tool execution
- **Moly**: User approval UI for each tool call

### 4. Usage Context
- **Dora**: Chat completions with MaaS providers
- **Moly**: Realtime voice conversations

## The Real Gap: MCP in Realtime API

The critical gap is not that Dora lacks MCP, but that:

1. **MCP is in `dora-maas-client`** (Chat API) not `dora-openai-websocket` (Realtime API)
2. **No integration between the two** - Realtime API can't use MCP tools
3. **Different APIs** - Chat Completions vs Realtime WebSocket

## Updated TODO: Bridge MCP to Realtime

### What Needs to Be Done

#### 1. Connect dora-maas-client MCP to dora-openai-websocket
```rust
// In dora-openai-websocket, import from dora-maas-client
use dora_maas_client::tool::{ToolSet, Tool};
use dora_maas_client::config::McpConfig;
```

#### 2. Add Tool Support to Realtime Session
```rust
// Add tools to SessionConfig
pub struct SessionConfig {
    // ... existing fields ...
    pub tools: Vec<serde_json::Value>,  // Currently empty!
    pub tool_choice: String,            // Currently unused!
}
```

#### 3. Implement Function Call Events
```rust
// Add missing events to OpenAIRealtimeResponse
#[serde(rename = "response.function_call_arguments.done")]
FunctionCallArgumentsDone {
    call_id: String,
    name: String,
    arguments: String,
}
```

#### 4. Create Tool Execution Pipeline
```rust
// Bridge to dora-maas-client's ToolSet
async fn execute_tool_call(
    tool_set: &ToolSet,
    name: &str,
    arguments: &str,
) -> Result<String> {
    let tool = tool_set.get_tool(name)?;
    let args = serde_json::from_str(arguments)?;
    let result = tool.call(args).await?;
    Ok(format_tool_result(result))
}
```

## Revised Implementation Plan

### Phase 1: Bridge MCP to Realtime (Week 1-2)
- [ ] Import dora-maas-client MCP components into dora-openai-websocket
- [ ] Initialize ToolSet during WebSocket session setup
- [ ] Register tools in SessionConfig
- [ ] Add tool discovery from MCP servers

### Phase 2: Function Calling Protocol (Week 3)
- [ ] Add function call event types
- [ ] Parse function calls from OpenAI responses
- [ ] Route to dora-maas-client's ToolSet
- [ ] Send results back to OpenAI

### Phase 3: Enhance MCP Features (Week 4)
- [ ] Add tool namespacing (optional but recommended)
- [ ] Implement tool approval mechanism
- [ ] Add tool execution logging
- [ ] Handle tool errors gracefully

### Phase 4: Testing & Integration (Week 5)
- [ ] Test with existing MCP servers (filesystem, weather, etc.)
- [ ] Ensure streaming compatibility
- [ ] Validate tool result formatting
- [ ] End-to-end testing

## Conclusion

**Good News**: Dora already has robust MCP support via `rmcp` SDK in `dora-maas-client`!

**The Gap**: MCP is not connected to the Realtime API (`dora-openai-websocket`)

**Solution**: Bridge the existing MCP implementation from `dora-maas-client` to `dora-openai-websocket`

**Effort**: ~5 weeks instead of 12 weeks (since MCP foundation exists)

**Key Advantages**:
- Dora uses newer rmcp version (0.3.2 vs Moly's 0.2.0)
- MCP implementation is tested and working
- Recent fixes show active maintenance
- Architecture allows code reuse

The main work is connecting two existing systems rather than building MCP from scratch!