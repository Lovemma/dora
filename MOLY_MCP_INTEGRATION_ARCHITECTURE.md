# Moly MCP Integration Architecture - OpenAI Realtime API Implementation

## Overview

Moly integrates the MCP (Model Context Protocol) Rust SDK (`rmcp`) to provide tool calling capabilities within the OpenAI Realtime API. This integration enables AI assistants to interact with external services through a standardized protocol.

## MCP Rust SDK (`rmcp`) Architecture

### Core Components

The MCP SDK provides:
- **`rmcp`**: Core protocol implementation with async runtime (tokio)
- **`rmcp-macros`**: Procedural macros for tool generation
- **Transport layers**: Multiple connection methods (HTTP, SSE, stdio)
- **Service management**: Client/server role handling

### Key Types from `rmcp`
```rust
// Tool definition with JSON schema
pub struct Tool {
    pub name: String,
    pub description: Option<String>,
    pub input_schema: Arc<Map<String, Value>>, // JSON Schema
}

// Tool execution
pub struct CallToolRequestParam {
    pub name: Cow<'static, str>,
    pub arguments: Option<Map<String, Value>>,
}

pub struct CallToolResult {
    pub content: Vec<ContentPart>,
    pub is_error: Option<bool>,
}
```

## Moly's MCP Integration Layer

### 1. MCP Manager (`moly-kit/src/mcp/mcp_manager.rs`)

The `McpManagerClient` is the central hub for MCP server management:

```rust
pub struct McpManagerClient {
    services: Arc<Mutex<HashMap<String, McpServiceHandle>>>, // Connected MCP servers
    registry: Arc<Mutex<ToolRegistry>>,                      // Tool namespace registry
    latest_tools: Vec<Tool>,                                 // Cached tools
}
```

#### Key Features:

**Tool Namespacing**: Prevents naming conflicts between servers
```rust
// Namespaced format: "server_id__tool_name"
"filesystem__read_file" → Server: filesystem, Tool: read_file
"mcp-internet-speed__test-speed" → Server: mcp-internet-speed, Tool: test-speed
```

**Server Management**:
```rust
pub async fn add_server(&self, id: &str, transport: McpTransport) -> Result<()> {
    // Supports multiple transports:
    // - HTTP (streaming)
    // - SSE (Server-Sent Events)
    // - Stdio (child process)
    
    let service = match transport {
        McpTransport::Http(url) => /* HTTP client */,
        McpTransport::Sse(url) => /* SSE client */,
        McpTransport::Stdio(command) => /* Child process */,
    };
    
    // Auto-discover tools on connection
    let tools = self.discover_tools_for_server(id).await?;
    self.registry.add_server_tools(id, tools);
}
```

**Tool Discovery & Registry**:
```rust
pub struct ToolRegistry {
    tools: HashMap<String, ToolRegistryEntry>,      // Namespaced → tool
    server_tools: HashMap<String, Vec<String>>,     // Server → tool names
}

pub struct ToolRegistryEntry {
    pub server_id: String,
    pub original_name: String,      // Original tool name on server
    pub namespaced_name: String,    // Globally unique name
    pub schema: Tool,               // Full tool definition
}
```

### 2. OpenAI Realtime Integration

#### Tool Registration During Session Creation

When creating a realtime session, MCP tools are converted to OpenAI format:

```rust
// In openai_realtime.rs
pub fn create_realtime_session(&self, bot_id: &BotId, tools: &[Tool]) {
    // Convert MCP tools to OpenAI realtime format
    let realtime_tools: Vec<Value> = tools.iter().map(|tool| {
        let mut parameters = (*tool.input_schema).clone();
        
        // OpenAI requirements:
        parameters.insert("additionalProperties", Value::Bool(false));
        
        if parameters.get("type") == Some(&Value::String("object")) {
            parameters.entry("properties").or_insert(Value::Object(Map::new()));
        }
        
        json!({
            "type": "function",
            "name": tool.name,              // Namespaced name
            "description": tool.description.unwrap_or(""),
            "parameters": Value::Object(parameters)
        })
    }).collect();
    
    // Include tools in session config
    let session_config = SessionConfig {
        tools: realtime_tools,
        tool_choice: if tools.is_empty() { "none" } else { "auto" },
        // ... other config
    };
}
```

#### Tool Call Flow

```
1. AI decides to call a tool
    ↓
2. OpenAI sends FunctionCallRequest event
    {
        "type": "response.function_call_arguments.done",
        "name": "filesystem__read_file",
        "call_id": "call_abc123",
        "arguments": "{\"path\": \"/tmp/data.txt\"}"
    }
    ↓
3. Moly receives via WebSocket
    ↓
4. Emit RealtimeEvent::FunctionCallRequest
    ↓
5. UI handles tool permission (approve/deny)
    ↓
6. If approved, execute via MCP Manager:
    - Parse namespaced name → (server_id, tool_name)
    - Find server in registry
    - Call tool on specific server
    - Get CallToolResult
    ↓
7. Send result back to OpenAI:
    RealtimeCommand::SendFunctionCallResult {
        call_id: "call_abc123",
        output: "File contents: ..."
    }
```

### 3. Tool Execution Pipeline

```rust
// In mcp_manager.rs
async fn call_tool(
    &self,
    namespaced_tool_name: &str,
    arguments: Map<String, Value>
) -> Result<CallToolResult> {
    // 1. Parse namespace
    let (server_id, original_tool_name) = parse_namespaced_tool_name(namespaced_tool_name)?;
    
    // 2. Validate tool exists
    let tool_entry = self.registry.get_tool_entry(namespaced_tool_name)
        .ok_or("Tool not found")?;
    
    // 3. Get server connection
    let service = self.services.get(&server_id)
        .ok_or("Server not connected")?;
    
    // 4. Execute on server
    let request = CallToolRequestParam {
        name: original_tool_name.into(),
        arguments: Some(arguments),
    };
    
    service.call_tool(request).await
}
```

### 4. UI Integration (`realtime.rs` widget)

The Realtime widget manages tool interactions:

```rust
impl Realtime {
    fn handle_function_call(&mut self, name: String, call_id: String, arguments: String) {
        // Store pending tool call
        self.pending_tool_call = Some(PendingToolCall {
            name: name.clone(),
            call_id,
            arguments,
        });
        
        // Show approval UI
        self.show_tool_permission_ui(cx);
    }
    
    fn approve_tool_call(&mut self, cx: &mut Cx) {
        if let Some(pending) = &self.pending_tool_call {
            // Parse arguments
            let args = parse_tool_arguments(&pending.arguments)?;
            
            // Execute via MCP manager
            let result = self.mcp_manager.execute_tool_call(
                &pending.name,
                &pending.call_id,
                args
            ).await;
            
            // Send result to OpenAI
            self.realtime_channel.command_sender.unbounded_send(
                RealtimeCommand::SendFunctionCallResult {
                    call_id: pending.call_id.clone(),
                    output: result.content,
                }
            );
        }
    }
}
```

## Architecture Benefits

### 1. **Protocol Abstraction**
- MCP provides a standard interface for tools
- Transport-agnostic (HTTP, SSE, stdio)
- Language-agnostic server implementations

### 2. **Namespace Isolation**
- Multiple servers can provide tools without conflicts
- Clear attribution of tool to server
- Easy server addition/removal

### 3. **Type Safety**
- Rust's type system ensures protocol compliance
- JSON Schema validation for tool arguments
- Compile-time guarantees via `rmcp` macros

### 4. **Scalability**
- Async/await throughout with tokio
- Connection pooling per server
- Lazy tool discovery

### 5. **Security**
- User approval required for tool execution
- Argument validation against schemas
- Server isolation (separate processes/connections)

## Example: Filesystem Tool Integration

```rust
// 1. MCP server exposes filesystem tools
[MCP Filesystem Server]
    ├── read_file(path: string)
    ├── write_file(path: string, content: string)
    └── list_directory(path: string)

// 2. Moly registers with namespace
[Moly Tool Registry]
    ├── filesystem__read_file
    ├── filesystem__write_file
    └── filesystem__list_directory

// 3. OpenAI sees namespaced tools
[OpenAI Realtime Session]
    tools: [
        {
            "name": "filesystem__read_file",
            "description": "Read file contents",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {"type": "string"}
                },
                "required": ["path"]
            }
        }
    ]

// 4. AI calls tool
AI: "I'll read the config file for you"
→ FunctionCall("filesystem__read_file", {"path": "/config.json"})

// 5. Moly routes to correct server
Moly → Parse: "filesystem" server, "read_file" tool
     → Execute on filesystem MCP server
     → Return result to AI
```

## Integration Points

### 1. **Protocol Conversion**
- MCP Tool → OpenAI function schema
- MCP CallToolResult → OpenAI function result
- Bidirectional type mapping

### 2. **Error Handling**
- Server disconnection gracefully handled
- Tool execution failures reported to AI
- Validation errors prevent execution

### 3. **Performance**
- Tool discovery cached per server
- Concurrent tool execution support
- Minimal overhead for protocol translation

## Summary

Moly's integration of the MCP Rust SDK provides a robust foundation for tool calling in the OpenAI Realtime API:

1. **MCP Manager** orchestrates multiple MCP servers
2. **Tool Registry** maintains namespaced tool catalog
3. **Protocol translation** bridges MCP and OpenAI formats
4. **UI integration** provides user control over tool execution
5. **Type-safe implementation** leverages Rust's guarantees

This architecture enables Moly to seamlessly extend AI capabilities through external tools while maintaining security, performance, and user control.