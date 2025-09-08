# OpenAI Realtime API Architectural Categorization

## Critical Analysis of API Responsibilities

### Category 1: Pure Protocol/Transport Layer
**Current Owner**: `dora-openai-websocket` (partially)
**Scope**: WebSocket mechanics and message framing only

#### Events That Belong Here:
- WebSocket connection establishment
- Authentication headers
- Message framing/deframing
- Base64 encoding/decoding of audio payloads
- WebSocket close/error handling

#### Events That DON'T Belong Here (but are currently handled):
- ❌ `session.created` - This is business logic, not protocol
- ❌ `response.create` - This is orchestration logic
- ❌ Model selection - This is configuration management

**Critical Issue**: dora-openai-websocket is doing too much. It should ONLY handle WebSocket transport, not business logic.

---

### Category 2: Session State Management (NOT just configuration!)
**Current Owner**: Scattered (BAD ARCHITECTURE!)
**Scope**: Runtime session lifecycle and state transitions

#### What Actually Belongs Here:
##### Session Lifecycle:
- `session.created` - Session instantiation
- `session.updated` - Configuration changes
- Session ID management
- Session termination

##### Configuration vs State (IMPORTANT DISTINCTION):
**Configuration** (static):
- `voice` selection (currently hardcoded)
- `model` selection (currently faked)
- `temperature` settings
- `max_tokens` limits

**State** (dynamic):
- Current conversation context
- Active response tracking
- Rate limit consumption
- Token usage accumulation

#### Architectural Problem:
No single component owns session state! It's scattered between:
- dora-openai-websocket (partial)
- maas-client (conversation history)
- No component tracks response state properly

**Recommendation**: Need a dedicated `session-manager` node

---

### Category 3: Tool/Function Management (MCP Layer)
**Current Owner**: `maas-client` (well-handled)
**Scope**: Tool discovery, registration, execution, namespacing

#### Well-Handled Events:
- Tool registration from MCP servers ✅
- Tool execution via MCP ✅
- Tool result formatting ✅

#### Missing/Problematic:
- ❌ `response.function_call_arguments.delta` - Not forwarded to client
- ❌ `response.function_call_arguments.done` - Not forwarded to client
- ❌ Tool namespacing not exposed in protocol
- ❌ Tool approval mechanism (automatic execution is risky)
- ❌ Function call streaming (currently buffered)

#### Critical Gap:
The protocol expects incremental streaming of function arguments, but maas-client buffers everything. This breaks real-time function calling UX.

---

### Category 4: Audio Pipeline & VAD
**Current Owners**: Multiple nodes (GOOD SEPARATION)
**Scope**: Audio processing, not protocol

#### Layer 4A: Audio Input Pipeline
**Owner**: `speech-monitor` → `asr`
- `input_audio_buffer.speech_started` (VAD detection)
- `input_audio_buffer.speech_stopped` (VAD detection)
- `input_audio_buffer.append` (audio streaming)
- `input_audio_buffer.commit` (segmentation)

#### Layer 4B: Audio Output Pipeline
**Owner**: `text-segmenter` → `primespeech`
- Text segmentation logic
- TTS processing
- Audio generation

#### Layer 4C: Audio Transcription
**Owner**: `asr`
- `conversation.item.input_audio_transcription.completed`
- `conversation.item.input_audio_transcription.failed`

#### What's Missing:
- ❌ Dynamic VAD configuration (hardcoded in speech-monitor)
- ❌ `input_audio_buffer.clear` - No way to cancel audio
- ❌ Audio format negotiation (PCM16 only)
- ❌ Transcription model selection (hardcoded)

---

### Category 5: Response Orchestration
**Current Owner**: NOBODY! (CRITICAL GAP)
**Scope**: Response lifecycle, streaming coordination, interruption

#### Orphaned Events (No Clear Owner):
- `response.created` - Who tracks this?
- `response.done` - Who knows when everything is done?
- `response.cancelled` - Who handles interruption?
- `response.output_item.added` - Who manages output items?
- `response.content_part.added` - Who tracks content parts?

#### Streaming Coordination Events:
- `response.audio.delta` - Currently handled but not tracked
- `response.text.delta` - Currently handled but not tracked
- `response.audio_transcript.delta` - Not implemented
- All `.done` events - Not properly tracked

**Critical Problem**: No component owns the response lifecycle! This causes:
- Can't cancel responses properly
- Can't track response completion
- Can't handle interruptions
- Can't coordinate multi-modal outputs

---

### Category 6: Conversation Management
**Current Owner**: Partially `maas-client` (inadequate)
**Scope**: Conversation history, context management, item lifecycle

#### What's Missing:
- ❌ `conversation.created` - No conversation ID tracking
- ❌ `conversation.item.created` - Items not properly tracked
- ❌ `conversation.item.deleted` - Can't remove items
- ❌ `conversation.item.truncate` - Can't manage context size
- ❌ Conversation persistence
- ❌ Context window management

**Problem**: maas-client maintains chat history for LLM context but doesn't expose it as conversation items to the protocol.

---

### Category 7: Error Handling & Observability
**Current Owner**: Each node individually (NO COORDINATION)
**Scope**: Error propagation, rate limits, metrics

#### What's Missing:
- ❌ `error` event propagation to client
- ❌ `rate_limits.updated` - No tracking at all
- ❌ Unified error handling strategy
- ❌ Cascading failure handling
- ❌ Circuit breakers
- ❌ Retry logic coordination

---

## Architectural Mismatches & Critical Gaps

### 1. **Response Lifecycle is Orphaned**
The biggest gap: Nobody owns response orchestration. This is why Dora can't properly handle:
- Response interruption
- Multi-modal coordination
- Completion tracking

### 2. **Session State is Scattered**
No central session manager means:
- Configuration is hardcoded in multiple places
- State isn't properly tracked
- Can't update session dynamically

### 3. **Event Routing is Implicit**
Events flow through dataflow but there's no explicit routing logic for protocol events. This makes it hard to:
- Forward events to clients
- Coordinate between nodes
- Handle event ordering

### 4. **No Protocol State Machine**
The OpenAI API has implicit state transitions (e.g., can't send audio during function call), but Dora has no state machine enforcing these rules.

### 5. **Streaming vs Buffering Mismatch**
OpenAI expects streaming everything (text, audio, function args), but Dora buffers at multiple points:
- maas-client buffers LLM responses
- text-segmenter buffers for TTS
- Function calls are atomic, not streamed

---

## Recommendations for Clean Architecture

### 1. Create Missing Components

#### `session-manager` Node (NEW)
**Owns**:
- Session lifecycle
- Configuration management
- State tracking
- Rate limits

#### `response-orchestrator` Node (NEW)
**Owns**:
- Response lifecycle
- Streaming coordination
- Interruption handling
- Multi-modal synchronization

#### `conversation-manager` Node (NEW)
**Owns**:
- Conversation history
- Context management
- Item lifecycle
- Truncation logic

### 2. Refactor Existing Components

#### `dora-openai-websocket`
**Should ONLY handle**:
- WebSocket transport
- Message framing
- Base64 encoding
- Authentication

**Should NOT handle**:
- Session logic
- Response creation
- Model selection

#### `maas-client`
**Keep**:
- LLM interaction
- MCP tool execution

**Add**:
- Function argument streaming
- Tool result streaming

**Remove**:
- Session management logic

### 3. Event Bus Architecture
Instead of point-to-point dataflow, consider an event bus where:
- All protocol events go through a central router
- Nodes subscribe to relevant events
- Protocol state machine enforces valid transitions

---

## Hard Truths

1. **Current architecture can't achieve 100% compliance** without major refactoring
2. **The dataflow model is fighting against the protocol's streaming nature**
3. **Missing components are more critical than enhancing existing ones**
4. **The protocol expects stateful coordination that Dora's stateless nodes can't provide**
5. **MCP integration is solid, but everything else needs work**

## Priority Order (Based on Impact)

1. **Response Orchestrator** - Without this, can't handle basic response lifecycle
2. **Session Manager** - Without this, can't configure dynamically
3. **Event Router** - Without this, can't properly forward protocol events
4. **Conversation Manager** - Without this, can't manage context
5. **Error Coordinator** - Without this, can't handle failures gracefully

This is the honest architectural assessment. The current Dora architecture has fundamental mismatches with the OpenAI Realtime API's expectations.