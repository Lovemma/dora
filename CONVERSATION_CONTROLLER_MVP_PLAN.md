# Conversation Controller - MVP Agile Implementation Plan

## Philosophy: Start Small, Iterate Fast

**MVP Goal**: Create the minimal controller that fixes the most critical issues while keeping existing nodes working.

## Sprint 0: What's Actually Broken? (Analysis)

### Critical Issues (MUST FIX in MVP):
1. ❌ **No response lifecycle tracking** → Can't cancel/interrupt
2. ❌ **No session state owner** → Can't update configuration
3. ❌ **No function call coordination** → MCP events not forwarded

### Working Fine (DON'T TOUCH):
- ✅ Audio pipeline (ASR/TTS)
- ✅ MCP tool execution
- ✅ WebSocket transport
- ✅ Basic conversation flow

## Sprint 1: Minimal Viable Controller (Week 1)

### Goal: Just Track What's Happening

```rust
// conversation_controller_v1.rs - MINIMAL implementation
pub struct ConversationControllerMVP {
    // Only track essential state
    session_id: String,
    current_response_id: Option<String>,
    is_function_calling: bool,
}
```

### MVP Dataflow Changes:
```yaml
nodes:
  # NEW: Minimal controller
  - id: conversation-controller
    path: conversation_controller_mvp
    inputs:
      # Only essential inputs
      websocket_event: NODE_ID/client_event
      function_call: maas-client/function_call_detected
      llm_complete: maas-client/response_complete
    outputs:
      # Only essential outputs
      - response_state     # Tell websocket what's happening
      - forward_function   # Forward function calls to client

  # EXISTING nodes stay the same
  - id: NODE_ID
    # ... no changes
  
  - id: maas-client
    # Add ONE new output
    outputs:
      - text
      - status
      - function_call_detected  # NEW: Just notify controller
```

### Implementation (2-3 days):
```rust
impl ConversationControllerMVP {
    async fn handle_event(&mut self, event: Event) -> Result<()> {
        match event {
            Event::Input { id: "websocket_event", data } => {
                // Just track that we're processing
                let event: ClientEvent = deserialize(data)?;
                if matches!(event, ClientEvent::ResponseCreate) {
                    self.current_response_id = Some(generate_id());
                    self.send_output("response_state", ResponseState::Started)?;
                }
            }
            Event::Input { id: "function_call", data } => {
                // Forward to websocket for protocol compliance
                self.is_function_calling = true;
                self.send_output("forward_function", data)?;
            }
            Event::Input { id: "llm_complete", .. } => {
                // Track completion
                if let Some(id) = self.current_response_id.take() {
                    self.send_output("response_state", ResponseState::Completed(id))?;
                }
                self.is_function_calling = false;
            }
        }
        Ok(())
    }
}
```

**Success Criteria**:
- [x] WebSocket knows when response starts/ends
- [x] Function calls are forwarded to client
- [x] Existing nodes still work

---

## Sprint 2: Add Interruption Support (Week 2)

### Goal: Handle Response Cancellation

```rust
pub struct ConversationControllerV2 {
    // Add interruption handling
    session_id: String,
    current_response_id: Option<String>,
    is_function_calling: bool,
    is_interrupted: bool,  // NEW
}
```

### New Inputs/Outputs:
```yaml
inputs:
  speech_started: speech-monitor/speech_started  # NEW: Detect interruption
  cancel_request: NODE_ID/cancel_request        # NEW: Explicit cancel
outputs:
  - cancel_downstream  # NEW: Tell nodes to stop
```

### Implementation (2 days):
```rust
Event::Input { id: "speech_started", .. } => {
    if self.current_response_id.is_some() {
        // User interrupted!
        self.is_interrupted = true;
        self.send_output("cancel_downstream", CancelCommand)?;
        self.send_output("response_state", ResponseState::Cancelled)?;
        self.current_response_id = None;
    }
}
```

**Success Criteria**:
- [x] Can interrupt AI responses
- [x] Downstream nodes stop processing
- [x] Client receives cancelled event

---

## Sprint 3: Dynamic Session Configuration (Week 3)

### Goal: Allow Runtime Configuration Changes

```rust
pub struct ConversationControllerV3 {
    // Add configuration management
    session_id: String,
    session_config: SessionConfig,  // NEW
    current_response_id: Option<String>,
    // ...
}

pub struct SessionConfig {
    voice: String,
    vad_threshold: f32,
    temperature: f32,
    // Only what we can actually change
}
```

### New Connections:
```yaml
inputs:
  session_update: NODE_ID/session_update  # NEW
outputs:
  - vad_config         # NEW: Update speech-monitor
  - tts_voice         # NEW: Update primespeech
  - llm_config        # NEW: Update maas-client
```

### Implementation (2 days):
```rust
Event::Input { id: "session_update", data } => {
    let update: SessionUpdate = deserialize(data)?;
    
    // Update our config
    self.session_config.merge(update);
    
    // Forward to relevant nodes
    if update.has_vad_changes() {
        self.send_output("vad_config", self.session_config.vad)?;
    }
    if update.has_voice_change() {
        self.send_output("tts_voice", self.session_config.voice)?;
    }
}
```

**Success Criteria**:
- [x] Can change voice at runtime
- [x] Can adjust VAD sensitivity
- [x] Settings persist during session

---

## Sprint 4: Basic Conversation Tracking (Week 4)

### Goal: Track Conversation History

```rust
pub struct ConversationControllerV4 {
    // Add conversation tracking
    session_id: String,
    session_config: SessionConfig,
    conversation_items: Vec<ConversationItem>,  // NEW
    current_response_id: Option<String>,
}
```

### Implementation (3 days):
```rust
impl ConversationControllerV4 {
    fn add_user_message(&mut self, text: String) {
        self.conversation_items.push(ConversationItem {
            id: generate_id(),
            role: "user",
            content: text,
            timestamp: now(),
        });
        
        // Keep last 20 items (simple truncation)
        if self.conversation_items.len() > 20 {
            self.conversation_items.remove(0);
        }
    }
}
```

**Success Criteria**:
- [x] Maintains conversation history
- [x] Simple FIFO truncation works
- [x] Can retrieve transcript

---

## Sprint 5: Function Call Result Handling (Week 5)

### Goal: Complete Function Call Flow

```rust
pub struct ConversationControllerV5 {
    // Add function result tracking
    pending_function_calls: HashMap<String, FunctionCall>,  // NEW
    // ... rest
}
```

### Implementation (2 days):
```rust
Event::Input { id: "function_result", data } => {
    let result: FunctionResult = deserialize(data)?;
    
    // Add to conversation
    self.conversation_items.push(ConversationItem {
        role: "function",
        content: result.output,
    });
    
    // Forward to client
    self.send_output("forward_function_result", result)?;
    
    // Continue conversation
    self.send_output("continue_after_function", true)?;
}
```

---

## Incremental Deployment Strategy

### Phase 1: Shadow Mode (Week 1)
- Deploy controller alongside existing system
- Controller observes but doesn't control
- Validate state tracking

### Phase 2: Partial Control (Week 2-3)
- Controller handles interruptions
- Controller forwards function calls
- Existing nodes still work independently

### Phase 3: Full Control (Week 4-5)
- Controller manages all state
- Controller coordinates responses
- Existing nodes become stateless executors

## Key Design Decisions for MVP

### What We're NOT Building (Yet):
- ❌ Complex state machine (just track basics)
- ❌ State persistence (restart = new session)
- ❌ Sophisticated context management (simple FIFO)
- ❌ Error recovery (fail fast)
- ❌ Performance optimization (correctness first)

### What We ARE Building:
- ✅ Response lifecycle tracking
- ✅ Interruption handling
- ✅ Dynamic configuration
- ✅ Function call coordination
- ✅ Basic conversation history

## Implementation Timeline

| Sprint | Duration | Feature | Risk | Value |
|--------|----------|---------|------|-------|
| 1 | 3 days | Basic tracking | Low | High |
| 2 | 2 days | Interruptions | Medium | Critical |
| 3 | 2 days | Configuration | Low | High |
| 4 | 3 days | History | Low | Medium |
| 5 | 2 days | Functions | Medium | High |

**Total MVP**: 12 days (2.5 weeks) of actual coding

## Success Metrics

### Sprint 1-2 (Core):
- Can track response lifecycle
- Can interrupt responses
- No regression in existing features

### Sprint 3-4 (Enhancement):
- Can change configuration at runtime
- Maintains conversation context
- Protocol events properly forwarded

### Sprint 5 (Completion):
- Function calls work end-to-end
- All critical gaps closed
- Ready for production testing

## Code Structure

```
conversation-controller/
├── Cargo.toml
├── src/
│   ├── main.rs           # Dora node entry
│   ├── controller.rs     # Core controller logic
│   ├── state.rs          # State definitions
│   ├── events.rs         # Event handling
│   └── utils.rs          # Helpers
```

## Minimal Cargo.toml
```toml
[package]
name = "conversation-controller"
version = "0.1.0"

[dependencies]
dora-node-api = "0.3"
tokio = { version = "1", features = ["full"] }
serde = { version = "1", features = ["derive"] }
serde_json = "1"
uuid = { version = "1", features = ["v4"] }
tracing = "0.1"
```

## Why This Approach Works

1. **Incremental Value**: Each sprint delivers working features
2. **Low Risk**: Not breaking existing functionality
3. **Fast Feedback**: Can test after each sprint
4. **Learning**: Discover real requirements by building
5. **Flexible**: Can adjust plan based on learnings

## Next Steps After MVP

Once MVP is working:
1. Add state persistence
2. Improve context management
3. Add comprehensive error handling
4. Optimize performance
5. Add monitoring/metrics

This MVP approach gets us a working conversation controller in 2-3 weeks that solves the critical issues while keeping the existing system functional.