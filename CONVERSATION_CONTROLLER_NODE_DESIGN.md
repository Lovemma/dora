# Conversation Controller Node Design for Dora

## Core Concept
The **Conversation Controller** is a stateful orchestration node that acts as the "brain" of the realtime conversation system, managing all session state, coordinating responses, and enforcing protocol rules.

## Architecture Overview

```
                    [Conversation Controller]
                    (Central State Machine)
                            ↑
        ┌───────────────────┼───────────────────┐
        ↓                   ↓                   ↓
[WebSocket Node]    [Audio Pipeline]    [LLM/MCP Node]
  (Transport)        (ASR/TTS/VAD)      (Intelligence)
```

## Main Functions

### 1. Session Lifecycle Management
```rust
pub struct SessionManager {
    session_id: String,
    state: SessionState,
    config: SessionConfig,
    created_at: Instant,
    last_activity: Instant,
}

pub enum SessionState {
    Initializing,
    Active,
    Processing,
    WaitingForFunction,
    Suspended,
    Terminating,
}
```

**Responsibilities**:
- Generate and track session IDs
- Manage session configuration (voice, model, tools, VAD settings)
- Handle session updates dynamically
- Track session timeout and cleanup

### 2. Response Orchestration
```rust
pub struct ResponseOrchestrator {
    active_response: Option<ResponseState>,
    response_queue: VecDeque<PendingResponse>,
    interrupt_handler: InterruptionStrategy,
}

pub struct ResponseState {
    id: String,
    status: ResponseStatus,
    start_time: Instant,
    outputs: Vec<OutputItem>,
    pending_functions: Vec<FunctionCall>,
}

pub enum ResponseStatus {
    Creating,
    WaitingForAudio,
    StreamingAudio,
    WaitingForFunction,
    Completing,
    Cancelled,
}
```

**Responsibilities**:
- Coordinate multi-modal responses
- Handle interruptions and cancellations
- Track response lifecycle events
- Manage function call flows

### 3. Conversation State Management
```rust
pub struct ConversationManager {
    conversation_id: String,
    items: Vec<ConversationItem>,
    context_window: ContextWindow,
    transcript: String,
}

pub struct ContextWindow {
    max_tokens: usize,
    current_tokens: usize,
    truncation_strategy: TruncationStrategy,
}

pub enum TruncationStrategy {
    FIFO,           // Remove oldest first
    Summarize,      // Summarize old content
    Selective,      // Keep important items
}
```

**Responsibilities**:
- Maintain conversation history
- Manage context window limits
- Handle item creation/deletion/truncation
- Track transcripts and metadata

### 4. Protocol State Machine
```rust
pub struct ProtocolStateMachine {
    current_state: ProtocolState,
    valid_transitions: HashMap<(ProtocolState, EventType), ProtocolState>,
    event_queue: VecDeque<ProtocolEvent>,
}

pub enum ProtocolState {
    Idle,
    ReceivingAudio,
    ProcessingInput,
    GeneratingResponse,
    StreamingOutput,
    ExecutingFunction,
    Error,
}
```

**Responsibilities**:
- Enforce valid state transitions
- Queue and order events properly
- Prevent invalid operations
- Handle error states

### 5. Event Coordination & Routing
```rust
pub struct EventCoordinator {
    routing_table: HashMap<EventType, Vec<NodeId>>,
    event_log: Vec<EventRecord>,
    pending_acks: HashMap<EventId, PendingAck>,
}

impl EventCoordinator {
    pub async fn route_event(&mut self, event: ProtocolEvent) -> Result<()> {
        // Validate event against current state
        self.validate_event(&event)?;
        
        // Log event
        self.log_event(&event);
        
        // Route to appropriate nodes
        for node_id in self.get_destinations(&event) {
            self.send_to_node(node_id, &event).await?;
        }
        
        // Track acknowledgment if needed
        if event.requires_ack() {
            self.track_pending_ack(&event);
        }
        
        Ok(())
    }
}
```

## Dora Implementation

### Node Definition (dataflow.yml)
```yaml
nodes:
  - id: conversation-controller
    build: cargo build --release -p dora-conversation-controller
    path: ../../target/release/dora-conversation-controller
    
    # Inputs from all nodes
    inputs:
      # From WebSocket
      client_event: websocket/client_event
      connection_status: websocket/connection_status
      
      # From Audio Pipeline
      speech_started: speech-monitor/speech_started
      speech_ended: speech-monitor/speech_ended
      vad_status: speech-monitor/vad_status
      transcription: asr/transcription
      tts_complete: primespeech/segment_complete
      
      # From LLM/MCP
      llm_response: maas-client/text
      llm_status: maas-client/status
      available_tools: maas-client/available_tools
      function_result: maas-client/function_call_result
      
    # Outputs to all nodes
    outputs:
      # To WebSocket
      - server_event          # Protocol events to send to client
      - session_config        # Current session configuration
      
      # To Audio Pipeline
      - vad_config           # Dynamic VAD settings
      - audio_control        # Start/stop/clear commands
      - transcription_config # ASR settings
      
      # To LLM/MCP
      - llm_request         # Text input with context
      - function_request    # Function call requests
      - conversation_context # Current conversation state
      
      # Control outputs
      - response_control    # Start/cancel/interrupt
      - error_event        # Error notifications
      - metrics            # Performance metrics
    
    env:
      LOG_LEVEL: INFO
      MAX_CONTEXT_TOKENS: 4096
      SESSION_TIMEOUT_MS: 300000  # 5 minutes
      ENABLE_STATE_PERSISTENCE: true
      STATE_CHECKPOINT_INTERVAL_MS: 10000
```

### Core Implementation Structure
```rust
// src/main.rs
use dora_node_api::{DoraNode, Event};
use std::collections::{HashMap, VecDeque};
use tokio::sync::RwLock;
use std::sync::Arc;

pub struct ConversationController {
    node: DoraNode,
    session_manager: Arc<RwLock<SessionManager>>,
    response_orchestrator: Arc<RwLock<ResponseOrchestrator>>,
    conversation_manager: Arc<RwLock<ConversationManager>>,
    state_machine: Arc<RwLock<ProtocolStateMachine>>,
    event_coordinator: Arc<RwLock<EventCoordinator>>,
}

impl ConversationController {
    pub async fn run(mut self) -> Result<()> {
        while let Some(event) = self.node.next_event().await? {
            match event {
                Event::Input { id, data } => {
                    self.handle_input(id, data).await?;
                }
                Event::Timer(timer_event) => {
                    self.handle_timer(timer_event).await?;
                }
                _ => {}
            }
        }
        Ok(())
    }
    
    async fn handle_input(&mut self, id: String, data: Vec<u8>) -> Result<()> {
        match id.as_str() {
            "client_event" => self.handle_client_event(data).await?,
            "speech_started" => self.handle_speech_started(data).await?,
            "speech_ended" => self.handle_speech_ended(data).await?,
            "transcription" => self.handle_transcription(data).await?,
            "llm_response" => self.handle_llm_response(data).await?,
            "function_result" => self.handle_function_result(data).await?,
            _ => {}
        }
        Ok(())
    }
}
```

### Key Implementation Features

#### 1. State Persistence
```rust
impl ConversationController {
    async fn checkpoint_state(&self) -> Result<()> {
        let state = ConversationState {
            session: self.session_manager.read().await.clone(),
            conversation: self.conversation_manager.read().await.clone(),
            response: self.response_orchestrator.read().await.clone(),
        };
        
        // Save to disk or distributed store
        self.save_state(state).await?;
        Ok(())
    }
    
    async fn restore_state(&mut self) -> Result<()> {
        if let Some(state) = self.load_state().await? {
            *self.session_manager.write().await = state.session;
            *self.conversation_manager.write().await = state.conversation;
            *self.response_orchestrator.write().await = state.response;
        }
        Ok(())
    }
}
```

#### 2. Interruption Handling
```rust
impl ConversationController {
    async fn handle_interruption(&mut self) -> Result<()> {
        // 1. Cancel current response
        if let Some(response) = self.response_orchestrator.write().await.active_response.take() {
            // Send cancel to all downstream nodes
            self.node.send_output("response_control", 
                ResponseControl::Cancel { response_id: response.id }
            ).await?;
            
            // Send cancelled event to client
            self.node.send_output("server_event",
                ServerEvent::ResponseCancelled { response_id: response.id }
            ).await?;
        }
        
        // 2. Clear audio buffers
        self.node.send_output("audio_control", 
            AudioControl::ClearBuffers
        ).await?;
        
        // 3. Transition state
        self.state_machine.write().await.transition(ProtocolState::ReceivingAudio)?;
        
        Ok(())
    }
}
```

#### 3. Function Call Coordination
```rust
impl ConversationController {
    async fn handle_function_call(&mut self, call: FunctionCall) -> Result<()> {
        // 1. Update state
        self.state_machine.write().await.transition(ProtocolState::ExecutingFunction)?;
        
        // 2. Track in response
        self.response_orchestrator.write().await
            .active_response.as_mut()
            .map(|r| r.pending_functions.push(call.clone()));
        
        // 3. Forward to MCP
        self.node.send_output("function_request", call).await?;
        
        // 4. Set timeout
        self.set_function_timeout(call.id, Duration::from_secs(30)).await?;
        
        Ok(())
    }
}
```

#### 4. Context Management
```rust
impl ConversationController {
    async fn manage_context(&mut self) -> Result<()> {
        let mut conv = self.conversation_manager.write().await;
        
        // Check token limit
        if conv.context_window.current_tokens > conv.context_window.max_tokens {
            match conv.context_window.truncation_strategy {
                TruncationStrategy::FIFO => {
                    // Remove oldest items
                    while conv.context_window.current_tokens > conv.context_window.max_tokens * 0.8 {
                        if let Some(item) = conv.items.first() {
                            let tokens = estimate_tokens(&item);
                            conv.items.remove(0);
                            conv.context_window.current_tokens -= tokens;
                            
                            // Notify client
                            self.node.send_output("server_event",
                                ServerEvent::ConversationItemDeleted { item_id: item.id }
                            ).await?;
                        }
                    }
                }
                TruncationStrategy::Summarize => {
                    // Summarize old content
                    let summary = self.summarize_old_items(&conv.items).await?;
                    conv.items = vec![summary];
                }
                _ => {}
            }
        }
        
        Ok(())
    }
}
```

## Integration Points

### 1. With WebSocket Node
```rust
// WebSocket forwards all client events
websocket_node.send_output("client_event", raw_event);

// Controller sends back server events
controller.on_output("server_event", |event| {
    websocket_node.send_to_client(event);
});
```

### 2. With Audio Pipeline
```rust
// Controller configures VAD dynamically
controller.send_output("vad_config", VadConfig {
    threshold: 0.5,
    silence_duration_ms: 500,
});

// Audio nodes report status
speech_monitor.send_output("speech_started", timestamp);
asr.send_output("transcription", text);
```

### 3. With LLM/MCP
```rust
// Controller sends contextualized requests
controller.send_output("llm_request", LLMRequest {
    text: user_input,
    context: conversation_history,
    tools: available_tools,
});

// MCP reports results
maas_client.send_output("function_result", result);
```

## Benefits of This Architecture

1. **Single Source of Truth**: All state in one place
2. **Protocol Compliance**: Enforces valid state transitions
3. **Clean Interfaces**: Clear contracts between nodes
4. **Fault Tolerance**: Can checkpoint and restore state
5. **Observability**: Central logging and metrics
6. **Extensibility**: Easy to add new features
7. **Testability**: Can unit test state machine

## Implementation Timeline

### Phase 1: Core Structure (Week 1)
- Basic node structure
- State management classes
- Event routing framework

### Phase 2: Session Management (Week 2)
- Session lifecycle
- Configuration handling
- Dynamic updates

### Phase 3: Response Orchestration (Week 3)
- Response tracking
- Interruption handling
- Multi-modal coordination

### Phase 4: Conversation Management (Week 4)
- History tracking
- Context windowing
- Item lifecycle

### Phase 5: Integration (Week 5)
- Connect to existing nodes
- Test end-to-end flows
- Performance optimization

This controller node design provides the missing orchestration layer that Dora needs for proper OpenAI Realtime API compliance while maintaining the benefits of the dataflow architecture.