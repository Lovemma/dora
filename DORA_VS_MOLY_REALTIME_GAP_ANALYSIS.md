# Dora vs Moly OpenAI Realtime API - Gap Analysis & TODO List

## Executive Summary

Dora's `dora-openai-websocket` provides basic OpenAI Realtime API connectivity but lacks many critical features that Moly has fully implemented. The most significant gaps are:
1. **No function/tool calling support**
2. **No MCP integration**
3. **Limited protocol coverage**
4. **No UI controls for session management**
5. **Missing advanced audio features**

## Feature Comparison Matrix

| Feature | Moly | Dora | Gap |
|---------|------|------|-----|
| **Core Protocol** |
| WebSocket connection | ✅ Full | ✅ Basic | Partial |
| Session management | ✅ Complete | ⚠️ Basic | Major |
| Error handling | ✅ Comprehensive | ⚠️ Basic | Major |
| Reconnection logic | ✅ Automatic | ❌ None | Critical |
| **Audio Processing** |
| Audio input (mic → AI) | ✅ Full pipeline | ✅ Basic | Minor |
| Audio output (AI → speaker) | ✅ Full pipeline | ✅ Basic | Minor |
| Resampling (24kHz ↔ 16kHz) | ✅ Efficient | ✅ Basic | Minor |
| Voice selection | ✅ 6 voices | ❌ Hardcoded | Major |
| Transcription model selection | ✅ 3 models | ❌ Hardcoded | Major |
| Noise reduction config | ✅ Configurable | ❌ None | Major |
| **Tool/Function Calling** |
| Function call support | ✅ Complete | ❌ None | Critical |
| MCP integration | ✅ Full rmcp SDK | ❌ None | Critical |
| Tool registry | ✅ Namespaced | ❌ None | Critical |
| Tool approval UI | ✅ Interactive | ❌ None | Critical |
| Tool result handling | ✅ Complete | ❌ None | Critical |
| **Session Features** |
| Turn detection (VAD) | ✅ Configurable | ⚠️ Hardcoded | Major |
| Interruption handling | ✅ Smart control | ⚠️ Basic | Major |
| Greeting generation | ✅ Dynamic | ❌ None | Major |
| Conversation history | ✅ Tracked | ❌ None | Major |
| **UI/UX** |
| Start/Stop controls | ✅ Interactive | ❌ Auto-start | Critical |
| Status indicators | ✅ Comprehensive | ❌ Console only | Major |
| Audio device selection | ✅ Dynamic | ❌ None | Major |
| Settings persistence | ✅ Preferences | ❌ None | Major |
| **Architecture** |
| Event-driven architecture | ✅ Full channels | ❌ Direct calls | Major |
| State management | ✅ Centralized | ❌ Scattered | Major |
| Type safety | ✅ Strong types | ⚠️ Partial | Major |
| Platform support | ✅ Multi-platform | ⚠️ Native only | Minor |

## Critical Gaps & Required Components

### 1. 🚨 **Function/Tool Calling System** (CRITICAL)
Dora completely lacks function calling support, which is essential for AI tool use.

**Missing Components:**
- Function call message types (`response.function_call_arguments.*`)
- Tool registration in session config
- Function call event handling
- Result submission mechanism

**Required Implementation:**
```rust
// Add to OpenAIRealtimeResponse enum
#[serde(rename = "response.function_call_arguments.done")]
FunctionCallArgumentsDone {
    response_id: String,
    item_id: String,
    call_id: String,
    name: String,
    arguments: String,
}

// Add function result submission
#[serde(rename = "conversation.item.create")]
ConversationItemCreate {
    item: FunctionCallOutputItem {
        id: String,
        type: "function_call_output",
        call_id: String,
        output: String,
    }
}
```

### 2. 🚨 **MCP Integration** (CRITICAL)
No MCP support means no external tool connectivity.

**Missing Components:**
- MCP manager client
- Tool discovery mechanism
- Tool namespace management
- Tool execution pipeline

**Required Implementation:**
- Integrate `rmcp` crate
- Create `McpManagerClient` equivalent
- Implement tool registry with namespacing
- Add transport support (HTTP/SSE/stdio)

### 3. ⚠️ **Event-Driven Architecture** (MAJOR)
Dora uses direct WebSocket handling instead of channels.

**Missing Components:**
- `RealtimeChannel` with event/command separation
- `RealtimeEvent` enum for UI communication
- `RealtimeCommand` enum for control flow
- Event routing system

**Required Implementation:**
```rust
pub struct RealtimeChannel {
    pub event_sender: UnboundedSender<RealtimeEvent>,
    pub event_receiver: Arc<Mutex<Option<UnboundedReceiver<RealtimeEvent>>>>,
    pub command_sender: UnboundedSender<RealtimeCommand>,
}
```

### 4. ⚠️ **Session Management** (MAJOR)
Limited control over session configuration.

**Missing Features:**
- Dynamic voice selection
- Transcription model selection
- Temperature control
- Max tokens configuration
- Instructions customization

### 5. ⚠️ **UI Controls** (MAJOR)
No user interface for controlling the realtime session.

**Missing Components:**
- Start/Stop button
- Voice selector dropdown
- Transcription model selector
- Interruption toggle
- Audio device selectors
- Status displays

## Detailed TODO List

### Phase 1: Core Protocol Enhancement (Week 1)
- [ ] **1.1** Add complete OpenAI message type definitions
  - [ ] Function call message types
  - [ ] Error response types
  - [ ] Conversation management types
  - [ ] Response status types
- [ ] **1.2** Implement event-driven architecture
  - [ ] Create `RealtimeChannel` struct
  - [ ] Define `RealtimeEvent` enum
  - [ ] Define `RealtimeCommand` enum
  - [ ] Setup bidirectional communication channels
- [ ] **1.3** Add proper error handling
  - [ ] WebSocket reconnection logic
  - [ ] Error event propagation
  - [ ] Graceful degradation

### Phase 2: Function Calling Support (Week 2)
- [ ] **2.1** Add function call protocol support
  - [ ] Parse function call requests from OpenAI
  - [ ] Create function call event types
  - [ ] Implement result submission protocol
- [ ] **2.2** Create tool management system
  - [ ] Tool registration interface
  - [ ] Tool execution framework
  - [ ] Result formatting
- [ ] **2.3** Add approval mechanism
  - [ ] Permission request events
  - [ ] Approval/denial handling
  - [ ] Security validation

### Phase 3: MCP Integration (Week 3)
- [ ] **3.1** Integrate rmcp SDK
  - [ ] Add rmcp dependency
  - [ ] Create MCP manager module
  - [ ] Implement transport layers
- [ ] **3.2** Build tool registry
  - [ ] Namespace management
  - [ ] Tool discovery
  - [ ] Dynamic tool loading
- [ ] **3.3** Connect to OpenAI session
  - [ ] Convert MCP tools to OpenAI format
  - [ ] Route function calls to MCP
  - [ ] Handle MCP responses

### Phase 4: Advanced Audio Features (Week 4)
- [ ] **4.1** Voice configuration
  - [ ] Add voice selection (alloy, echo, fable, onyx, nova, shimmer)
  - [ ] Persist voice preferences
  - [ ] Real-time voice switching
- [ ] **4.2** Transcription options
  - [ ] Model selection (whisper-1, gpt-4o-transcribe, etc.)
  - [ ] Language detection
  - [ ] Accuracy settings
- [ ] **4.3** Audio enhancements
  - [ ] Noise reduction configuration
  - [ ] Echo cancellation
  - [ ] Gain control

### Phase 5: Session Management (Week 5)
- [ ] **5.1** Session lifecycle
  - [ ] Proper session initialization
  - [ ] Session update mechanism
  - [ ] Clean shutdown
- [ ] **5.2** Configuration management
  - [ ] Temperature control
  - [ ] Max tokens setting
  - [ ] Instructions customization
  - [ ] Tool choice strategies
- [ ] **5.3** Conversation tracking
  - [ ] Message history
  - [ ] Transcript storage
  - [ ] Context management

### Phase 6: UI/UX Implementation (Week 6)
- [ ] **6.1** Control interface
  - [ ] Start/Stop button
  - [ ] Settings panel
  - [ ] Status indicators
- [ ] **6.2** Audio controls
  - [ ] Device selection
  - [ ] Volume controls
  - [ ] Mute/unmute
- [ ] **6.3** Tool approval UI
  - [ ] Permission dialogs
  - [ ] Tool status display
  - [ ] Execution feedback

### Phase 7: Testing & Polish (Week 7)
- [ ] **7.1** Integration testing
  - [ ] End-to-end tool calling
  - [ ] MCP server connectivity
  - [ ] Audio pipeline validation
- [ ] **7.2** Performance optimization
  - [ ] Audio latency reduction
  - [ ] Memory usage optimization
  - [ ] CPU usage profiling
- [ ] **7.3** Documentation
  - [ ] API documentation
  - [ ] Integration guides
  - [ ] Example implementations

## Implementation Priority

### 🔴 Critical (Must Have - Weeks 1-3)
1. Event-driven architecture
2. Function calling protocol
3. MCP integration basics
4. Start/Stop controls

### 🟡 Important (Should Have - Weeks 4-5)
1. Voice selection
2. Tool approval UI
3. Session configuration
4. Error recovery

### 🟢 Nice to Have (Could Have - Weeks 6-7)
1. Advanced audio features
2. Conversation history
3. Settings persistence
4. Performance optimizations

## Technical Dependencies

### Required Crates
```toml
[dependencies]
# MCP Support
rmcp = { version = "0.2.0", features = ["server"] }

# Async Runtime
tokio = { version = "1.0", features = ["full"] }
futures = "0.3"

# Serialization
serde = { version = "1.0", features = ["derive"] }
serde_json = "1.0"

# WebSocket
tokio-tungstenite = "0.20"

# UI (if adding controls)
makepad-widgets = { version = "*", optional = true }
```

### File Structure Changes
```
dora-openai-websocket/
├── src/
│   ├── main.rs           # Entry point
│   ├── protocol.rs        # [NEW] Protocol definitions
│   ├── realtime.rs        # [NEW] Realtime channel management
│   ├── mcp/
│   │   ├── mod.rs         # [NEW] MCP module
│   │   ├── manager.rs     # [NEW] MCP manager
│   │   └── registry.rs    # [NEW] Tool registry
│   ├── audio/
│   │   ├── mod.rs         # [NEW] Audio module
│   │   └── processor.rs   # [NEW] Audio processing
│   └── ui/
│       ├── mod.rs         # [NEW] UI module
│       └── controls.rs    # [NEW] UI controls
```

## Migration Strategy

### Step 1: Parallel Development
- Keep existing functionality intact
- Build new features in separate modules
- Use feature flags for gradual rollout

### Step 2: Integration Testing
- Test with simple tools first
- Validate audio pipeline changes
- Ensure backward compatibility

### Step 3: Gradual Rollout
- Enable features one by one
- Monitor performance impact
- Gather user feedback

## Risk Assessment

### High Risk Areas
1. **MCP Integration Complexity**: Tool calling requires significant architecture changes
2. **Audio Synchronization**: Managing multiple audio streams with interruptions
3. **State Management**: Complex state coordination between components

### Mitigation Strategies
1. Start with simple, stateless tools
2. Implement comprehensive logging
3. Add fallback mechanisms for each feature
4. Extensive testing at each phase

## Success Metrics

- [ ] Successfully execute MCP tools through OpenAI Realtime
- [ ] Audio latency < 200ms for interruptions
- [ ] Zero WebSocket disconnections during normal operation
- [ ] Tool execution success rate > 95%
- [ ] User-controlled session management
- [ ] Feature parity with Moly implementation

## Conclusion

Dora's current implementation provides a basic foundation but requires substantial enhancements to match Moly's capabilities. The most critical gap is the complete absence of function/tool calling support and MCP integration. With the structured approach outlined above, these gaps can be systematically addressed over a 7-week development period.