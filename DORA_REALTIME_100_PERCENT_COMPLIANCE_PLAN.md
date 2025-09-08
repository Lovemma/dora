# Dora Dataflow-Based OpenAI Realtime API 100% Compliance Plan

## Current Architecture Overview

### Dora Dataflow Pipeline
```
[Moly Client] 
    ↓ WebSocket (OpenAI Realtime Protocol)
[dora-openai-websocket] (Protocol Handler & Router)
    ├→ audio_out → [speech-monitor] → [asr] → text → [maas-client]
    │                                                      ↓ (MCP calls)
    │                                                  [MCP Servers]
    │                                                      ↓ (results)
    └← audio_in ← [primespeech] ← [text-segmenter] ← [maas-client]
```

### Current Node Responsibilities

| Node | Current Role | Protocol Handling |
|------|--------------|-------------------|
| **dora-openai-websocket** | WebSocket server, protocol negotiation, audio I/O routing | Partial OpenAI Realtime |
| **speech-monitor** | VAD, speech detection, segmentation | Internal Dora events |
| **asr** | Speech-to-text (FunASR/Whisper) | Internal Dora events |
| **maas-client** | LLM interaction, MCP tool execution | OpenAI Chat API + MCP |
| **text-segmenter** | Text chunking for TTS | Internal Dora events |
| **primespeech** | Text-to-speech | Internal Dora events |

## Gap Analysis for 100% Compliance

### 1. Protocol Gaps in dora-openai-websocket

| Feature | Current | Required | Location |
|---------|---------|----------|----------|
| **Session Management** | Basic | Full lifecycle | dora-openai-websocket |
| **Function Calls** | None | Full support | dora-openai-websocket ↔ maas-client |
| **Response Lifecycle** | Partial | Complete tracking | dora-openai-websocket |
| **Conversation State** | None | Full history | dora-openai-websocket |
| **Error Handling** | Basic | Comprehensive | All nodes |
| **Rate Limiting** | None | Token tracking | dora-openai-websocket |

### 2. MCP Integration Gaps

| Component | Current | Required | Solution |
|-----------|---------|----------|----------|
| **Tool Registration** | maas-client only | Exposed to WebSocket | Bridge via Dora events |
| **Function Call Events** | Not passed through | Full protocol support | New event types |
| **Tool Results** | Internal to maas-client | Sent to client | Result forwarding |
| **Tool Approval** | Automatic | Optional UI approval | New control events |

## Detailed Implementation Plan

### Phase 1: Protocol Event Bridge (Week 1-2)

#### 1.1 Extend Dora Event Types
Create new event types for OpenAI Realtime protocol compliance:

**File**: `dora-openai-websocket/src/protocol_events.rs` (NEW)
```rust
// OpenAI Realtime Protocol Events as Dora Events
pub enum DoraRealtimeEvent {
    // Session Events
    SessionCreated { session_id: String, config: SessionConfig },
    SessionUpdated { session_id: String, config: SessionConfig },
    
    // Function Call Events
    FunctionCallRequested {
        call_id: String,
        name: String,
        arguments: String,
        response_id: String,
    },
    FunctionCallCompleted {
        call_id: String,
        result: String,
    },
    
    // Response Events
    ResponseCreated { response_id: String },
    ResponseDone { response_id: String },
    ResponseCancelled { response_id: String },
    
    // Conversation Events
    ConversationItemCreated { item_id: String, content: Value },
    ConversationItemDeleted { item_id: String },
    
    // Rate Limit Events
    RateLimitsUpdated { limits: RateLimits },
}
```

#### 1.2 Update dora-openai-websocket Main Loop
**File**: `dora-openai-websocket/src/main.rs`
```rust
// Add new outputs to dataflow
outputs:
  - audio
  - text
  - function_call_request  // NEW
  - session_event          // NEW
  - response_event         // NEW
  - conversation_event     // NEW

// Handle incoming OpenAI messages
match openai_message {
    // Existing audio/text handling...
    
    // NEW: Function call handling
    OpenAIRealtimeResponse::FunctionCallArgumentsDone { call_id, name, arguments, .. } => {
        // Forward to maas-client via Dora event
        node.send_output(
            "function_call_request",
            FunctionCallRequest {
                call_id,
                name,
                arguments,
            }.into_arrow()
        ).await?;
    }
}
```

### Phase 2: MCP Tool Bridge (Week 2-3)

#### 2.1 Expose MCP Tools from maas-client
**File**: `dora-maas-client/src/main.rs`
```rust
// Add new outputs
outputs:
  - text
  - status
  - log
  - available_tools      // NEW: Send tool definitions
  - function_call_result // NEW: Send results back

// On initialization, send available tools
async fn initialize_tools(node: &mut DoraNode, tool_set: &ToolSet) {
    let tools = tool_set.get_tool_definitions();
    node.send_output(
        "available_tools",
        ToolDefinitions { tools }.into_arrow()
    ).await?;
}

// Handle function call requests
match event {
    Event::Input { id: "function_call_request", data } => {
        let request: FunctionCallRequest = data.from_arrow()?;
        
        // Execute tool
        let result = tool_set.execute_tool(&request.name, &request.arguments).await?;
        
        // Send result back
        node.send_output(
            "function_call_result",
            FunctionCallResult {
                call_id: request.call_id,
                result: result.to_string(),
            }.into_arrow()
        ).await?;
    }
}
```

#### 2.2 Register Tools in WebSocket Session
**File**: `dora-openai-websocket/src/main.rs`
```rust
// Add new input
inputs:
  available_tools: maas-client/available_tools
  function_call_result: maas-client/function_call_result

// When receiving tools from maas-client
Event::Input { id: "available_tools", data } => {
    let tools: ToolDefinitions = data.from_arrow()?;
    
    // Convert to OpenAI format
    let openai_tools = tools.to_openai_format();
    
    // Update session configuration
    session_config.tools = openai_tools;
    
    // Send session.update to client
    ws.send(OpenAIRealtimeMessage::SessionUpdate {
        session: session_config,
    }).await?;
}

// When receiving function results
Event::Input { id: "function_call_result", data } => {
    let result: FunctionCallResult = data.from_arrow()?;
    
    // Send to OpenAI client
    ws.send(OpenAIRealtimeMessage::ConversationItemCreate {
        item: ConversationItem {
            type: "function_call_output",
            call_id: result.call_id,
            output: result.result,
        }
    }).await?;
}
```

### Phase 3: Response & Conversation Management (Week 3-4)

#### 3.1 Response Lifecycle Tracking
**File**: `dora-openai-websocket/src/response_manager.rs` (NEW)
```rust
pub struct ResponseManager {
    active_responses: HashMap<String, ResponseState>,
    conversation_history: Vec<ConversationItem>,
}

impl ResponseManager {
    pub fn create_response(&mut self, id: String) -> ResponseCreatedEvent {
        self.active_responses.insert(id.clone(), ResponseState::InProgress);
        ResponseCreatedEvent { response_id: id }
    }
    
    pub fn complete_response(&mut self, id: String) -> ResponseDoneEvent {
        self.active_responses.insert(id, ResponseState::Completed);
        ResponseDoneEvent { response_id: id }
    }
    
    pub fn cancel_response(&mut self, id: String) -> ResponseCancelledEvent {
        self.active_responses.remove(&id);
        ResponseCancelledEvent { response_id: id }
    }
}
```

#### 3.2 Conversation State Management
**File**: `dora-openai-websocket/src/conversation.rs` (NEW)
```rust
pub struct ConversationManager {
    conversation_id: String,
    items: Vec<ConversationItem>,
    transcript: String,
}

impl ConversationManager {
    pub fn add_user_message(&mut self, text: String, audio: Option<Vec<u8>>) {
        self.items.push(ConversationItem {
            role: "user",
            content: vec![
                ContentPart::Text { text },
                ContentPart::Audio { audio },
            ],
        });
    }
    
    pub fn add_assistant_message(&mut self, text: String, audio: Option<Vec<u8>>) {
        self.items.push(ConversationItem {
            role: "assistant",
            content: vec![
                ContentPart::Text { text },
                ContentPart::Audio { audio },
            ],
        });
    }
}
```

### Phase 4: VAD Configuration Bridge (Week 4)

#### 4.1 Dynamic VAD Configuration
**File**: `dora-openai-websocket/src/main.rs`
```rust
// Add output for VAD control
outputs:
  - vad_config  // NEW

// When receiving session.update from client
OpenAIRealtimeMessage::SessionUpdate { session } => {
    if let Some(turn_detection) = session.turn_detection {
        // Forward to speech-monitor
        node.send_output(
            "vad_config",
            VadConfig {
                enabled: turn_detection.enabled,
                threshold: turn_detection.threshold,
                silence_duration_ms: turn_detection.silence_duration_ms,
                prefix_padding_ms: turn_detection.prefix_padding_ms,
            }.into_arrow()
        ).await?;
    }
}
```

**File**: `dora-speechmonitor/src/main.py`
```python
# Add input for dynamic configuration
def handle_input(event):
    if event.id == "vad_config":
        config = event.data
        self.vad_threshold = config["threshold"]
        self.silence_duration_ms = config["silence_duration_ms"]
        self.prefix_padding_ms = config["prefix_padding_ms"]
```

### Phase 5: Transcription Integration (Week 5)

#### 5.1 Input Audio Transcription Events
**File**: `dora-openai-websocket/src/main.rs`
```rust
// When receiving transcription from ASR
Event::Input { id: "transcription", data } => {
    let transcript: String = data.from_arrow()?;
    
    // Send transcription completed event
    ws.send(OpenAIRealtimeMessage::ConversationItemInputAudioTranscriptionCompleted {
        item_id: current_item_id,
        transcript,
    }).await?;
}
```

### Phase 6: Error Handling & Rate Limiting (Week 5-6)

#### 6.1 Comprehensive Error Handling
**File**: `dora-openai-websocket/src/error_handler.rs` (NEW)
```rust
pub struct ErrorHandler {
    retry_strategy: ExponentialBackoff,
    error_log: Vec<ErrorEvent>,
}

impl ErrorHandler {
    pub async fn handle_error(&mut self, error: DoraError) -> Result<Recovery> {
        match error {
            DoraError::WebSocketDisconnect => {
                self.retry_strategy.retry_connection().await
            }
            DoraError::NodeFailure(node_id) => {
                self.restart_node(node_id).await
            }
            DoraError::RateLimit(limits) => {
                self.apply_backpressure(limits).await
            }
        }
    }
}
```

#### 6.2 Rate Limit Tracking
```rust
pub struct RateLimitTracker {
    text_tokens_used: usize,
    audio_tokens_used: usize,
    requests_count: usize,
    reset_time: Instant,
}
```

### Phase 7: Testing & Validation (Week 6)

#### 7.1 Protocol Compliance Tests
```rust
#[cfg(test)]
mod tests {
    #[test]
    fn test_session_lifecycle() {
        // Test complete session create/update/destroy
    }
    
    #[test]
    fn test_function_calling_flow() {
        // Test function call request → execution → result
    }
    
    #[test]
    fn test_response_lifecycle() {
        // Test response create/done/cancel
    }
}
```

## Dataflow YAML Updates

### Updated whisper-template.yml
```yaml
nodes:
  - id: NODE_ID  # WebSocket server (enhanced)
    build: cargo build --release -p dora-openai-websocket
    path: dynamic
    inputs:
      audio: primespeech/audio
      text: asr/transcription
      speech_started: speech-monitor/speech_started
      speech_ended: speech-monitor/speech_ended
      available_tools: maas-client/available_tools        # NEW
      function_call_result: maas-client/function_call_result  # NEW
      response_status: maas-client/response_status       # NEW
    outputs:
      - audio
      - text
      - function_call_request  # NEW
      - vad_config            # NEW
      - session_config        # NEW

  - id: speech-monitor
    # ... existing config ...
    inputs:
      audio:
        source: NODE_ID/audio
      vad_config: NODE_ID/vad_config  # NEW: Dynamic VAD config

  - id: maas-client  # Enhanced with MCP bridging
    inputs:
      text: asr/transcription
      text_to_audio: NODE_ID/text
      function_call_request: NODE_ID/function_call_request  # NEW
    outputs:
      - text
      - status
      - log
      - available_tools        # NEW
      - function_call_result   # NEW
      - response_status       # NEW
```

## Implementation Timeline

| Week | Phase | Components | Deliverables |
|------|-------|------------|--------------|
| 1-2 | Protocol Bridge | dora-openai-websocket | Event types, message routing |
| 2-3 | MCP Integration | maas-client ↔ websocket | Tool registration, execution |
| 3-4 | State Management | Response & conversation | Lifecycle tracking |
| 4 | VAD Config | speech-monitor | Dynamic configuration |
| 5 | Transcription | ASR integration | Input audio events |
| 5-6 | Production | Error handling, rate limits | Resilience |
| 6 | Testing | All components | Compliance validation |

## Key Design Principles

1. **Minimal Changes**: Leverage existing dataflow, add bridge events
2. **Node Autonomy**: Each node maintains its responsibility
3. **Event-Driven**: Use Dora events for all protocol bridging
4. **Backward Compatible**: Existing functionality preserved
5. **Incremental**: Each phase independently testable

## Success Metrics

- [ ] 100% OpenAI Realtime API event coverage
- [ ] Full MCP tool support through dataflow
- [ ] < 50ms event routing latency
- [ ] Zero message loss during node failures
- [ ] Complete conversation state tracking
- [ ] Dynamic VAD configuration
- [ ] Comprehensive error recovery

## Risk Mitigation

1. **Event Ordering**: Use sequence numbers for guaranteed ordering
2. **Backpressure**: Implement flow control between nodes
3. **State Sync**: Periodic state snapshots for recovery
4. **Tool Timeouts**: Set limits on MCP execution time
5. **Circuit Breakers**: Prevent cascade failures

## Testing Strategy

1. **Unit Tests**: Each node's protocol handling
2. **Integration Tests**: End-to-end dataflow
3. **Protocol Tests**: OpenAI API compliance
4. **Load Tests**: Concurrent sessions
5. **Failure Tests**: Node restart scenarios

This plan provides a systematic approach to achieving 100% OpenAI Realtime API compliance while maintaining Dora's dataflow architecture. The key insight is using Dora events as a bridge between the WebSocket protocol and the distributed nodes, allowing each component to maintain its specialized role while collectively implementing the full protocol.