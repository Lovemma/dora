# Moly OpenAI Realtime API - Complete Architecture & Implementation

## Overview

Moly is a Rust-based chat application built with Makepad framework that implements OpenAI's Realtime API for voice conversations. It provides a native desktop UI with real-time audio streaming, voice activity detection, and WebSocket-based communication.

## Architecture Layers

### 1. Core Application Layer (`/src`)

#### Main Components:
- **`chat/chat_screen.rs`**: Main chat interface orchestrating UI and data flow
- **`data/store.rs`**: Central state management for the application
- **`data/providers.rs`**: Provider management for different AI services (OpenAI, local models)
- **`settings/`**: Configuration screens for providers and settings

### 2. Protocol & Client Layer (`/moly-kit/src`)

#### Key Files:

##### `protocol.rs` - Core Protocol Definitions
```rust
// Upgrade types for communication modes
pub enum Upgrade {
    Realtime(RealtimeChannel),
}

// Bidirectional channel for realtime communication
pub struct RealtimeChannel {
    pub event_sender: UnboundedSender<RealtimeEvent>,
    pub event_receiver: Arc<Mutex<Option<UnboundedReceiver<RealtimeEvent>>>>,
    pub command_sender: UnboundedSender<RealtimeCommand>,
}

// Events from server to UI
pub enum RealtimeEvent {
    SessionReady,
    AudioData(Vec<u8>),              // PCM16 audio chunks
    AudioTranscript(String),          // Delta text
    AudioTranscriptCompleted(String, String),
    UserTranscriptCompleted(String, String),
    SpeechStarted,
    SpeechStopped,
    ResponseCompleted,
    FunctionCallRequest { name, call_id, arguments },
    Error(String),
}

// Commands from UI to server
pub enum RealtimeCommand {
    StopSession,
    SendAudio(Vec<u8>),
    SendText(String),
    Interrupt,
    UpdateSessionConfig { voice, transcription_model },
    CreateGreetingResponse,
    SendFunctionCallResult { call_id, output },
}
```

##### `clients/openai_realtime.rs` - OpenAI Client Implementation
```rust
pub struct OpenAIRealtimeClient {
    address: String,
    api_key: Option<String>,
}

// WebSocket message types matching OpenAI API
pub enum OpenAIRealtimeMessage {
    SessionUpdate { session: SessionConfig },
    InputAudioBufferAppend { audio: String },  // base64
    InputAudioBufferCommit,
    ResponseCreate { response: ResponseConfig },
    ConversationItemCreate { item: Value },
    ConversationItemTruncate { item_id, content_index, audio_end_ms },
}

// Session configuration
pub struct SessionConfig {
    pub modalities: Vec<String>,        // ["text", "audio"]
    pub voice: String,                  // "alloy", "echo", etc.
    pub model: String,                  // "gpt-4o-realtime-preview"
    pub input_audio_format: String,     // "pcm16"
    pub output_audio_format: String,    // "pcm16"
    pub turn_detection: Option<TurnDetectionConfig>,
    pub tools: Vec<Value>,
    pub temperature: f32,
}
```

### 3. UI Widget Layer (`/moly-kit/src/widgets`)

##### `realtime.rs` - Main Realtime UI Component
```rust
pub struct Realtime {
    // Audio handling
    audio_buffer: Arc<Mutex<Vec<f32>>>,
    playback_audio: Arc<Mutex<Vec<f32>>>,
    is_recording: Arc<Mutex<bool>>,
    is_playing: Arc<Mutex<bool>>,
    
    // Realtime state
    realtime_channel: Option<RealtimeChannel>,
    conversation_active: bool,
    ai_is_responding: bool,
    user_is_interrupting: bool,
    
    // UI components
    view: View,
    audio_streaming_timer: Option<Timer>,
}
```

## Data Flow Architecture

### 1. Connection Establishment Flow
```
User clicks "Start Conversation"
    ↓
Realtime::start_conversation()
    ↓
OpenAIRealtimeClient::create_realtime_session()
    ↓
WebSocket handshake with headers:
- Authorization: Bearer {api_key}
- OpenAI-Beta: realtime=v1
    ↓
Create bidirectional channels (event/command)
    ↓
Spawn WebSocket read/write tasks
    ↓
Send SessionUpdate message
    ↓
Receive SessionCreated → emit SessionReady event
```

### 2. Audio Input Flow (User → AI)
```
Microphone input (24kHz)
    ↓
Audio callback captures samples
    ↓
Store in audio_buffer (Arc<Mutex<Vec<f32>>>)
    ↓
Timer triggers send_audio_chunk_to_realtime()
    ↓
Downsample: 24kHz → 16kHz (SincFixedIn resampler)
    ↓
Convert: f32 → i16 PCM
    ↓
RealtimeCommand::SendAudio(bytes)
    ↓
Base64 encode
    ↓
Send InputAudioBufferAppend via WebSocket
```

### 3. Audio Output Flow (AI → User)
```
WebSocket receives ResponseAudioDelta
    ↓
Base64 decode audio data
    ↓
Emit RealtimeEvent::AudioData(bytes)
    ↓
Convert: i16 PCM → f32
    ↓
Add to playback_audio buffer
    ↓
Audio callback consumes from buffer
    ↓
Output to speaker (24kHz)
```

### 4. Voice Activity Detection & Interruption
```
Server-side VAD detects speech:
- input_audio_buffer.speech_started → SpeechStarted event
- input_audio_buffer.speech_stopped → SpeechStopped event

On SpeechStarted (user interrupting):
1. Clear playback buffer (stop AI audio)
2. Set user_is_interrupting = true
3. Resume recording immediately

On receiving AI audio:
- If interruptions disabled: mute mic during AI speech
- If interruptions enabled: keep mic active for real-time interruption
```

## Key Implementation Details

### Audio Processing

#### Resampling Configuration
```rust
// Downsampler: 24kHz → 16kHz for OpenAI
let downsampler = SincFixedIn::<f32>::new(
    16000.0 / 24000.0,  // Ratio: 2/3
    2.0,                // Max delay
    SincInterpolationParameters {
        sinc_len: 256,
        f_cutoff: 0.95,
        interpolation: SincInterpolationType::Linear,
        oversampling_factor: 256,
        window: WindowFunction::BlackmanHarris2,
    },
    DOWNSAMPLE_CHUNK_SIZE,  // 480 samples
    1,                      // Mono
);
```

#### Audio Format Conversion
```rust
// f32 → i16 PCM for OpenAI
fn convert_f32_to_i16(samples: &[f32]) -> Vec<u8> {
    samples.iter()
        .flat_map(|&sample| {
            let clamped = sample.clamp(-1.0, 1.0);
            let i16_val = (clamped * 32767.0) as i16;
            i16_val.to_le_bytes()
        })
        .collect()
}

// i16 PCM → f32 for playback
fn convert_i16_to_f32(bytes: &[u8]) -> Vec<f32> {
    bytes.chunks_exact(2)
        .map(|chunk| {
            let i16_val = i16::from_le_bytes([chunk[0], chunk[1]]);
            i16_val as f32 / 32768.0
        })
        .collect()
}
```

### WebSocket Protocol

#### Message Flow
1. **Session initialization**: `session.update` with config
2. **Audio streaming**: `input_audio_buffer.append` with base64 PCM16
3. **Commit audio**: `input_audio_buffer.commit` to trigger processing
4. **Receive responses**: Various response types (audio, text, function calls)

#### Error Handling
- Automatic reconnection on disconnect
- Graceful degradation when audio devices unavailable
- Error events propagated to UI for user feedback

### State Management

#### Conversation State Machine
```
IDLE → CONNECTING → ACTIVE → STOPPED
         ↓            ↓
      ERROR ←────────┘
```

#### Audio State Coordination
- `is_recording`: Microphone capture state
- `is_playing`: Audio playback state
- `ai_is_responding`: AI generating response
- `user_is_interrupting`: User speaking during AI response

### UI Components

#### Main Controls
- Start/Stop button for conversation
- Voice selector (alloy, echo, fable, onyx, nova, shimmer)
- Transcription model selector (whisper-1, gpt-4o-transcribe)
- Interruption toggle (enable/disable)
- Audio device selectors (mic/speaker)

#### Status Indicators
- Connection status (connecting/connected/error)
- Activity status (listening/speaking/playing)
- Audio levels visualization
- Transcript display

## Performance Optimizations

1. **Lock-free audio buffers**: Using Arc<Mutex> with try_lock to avoid blocking
2. **Efficient resampling**: Fixed-size chunks with pre-allocated buffers
3. **Minimal latency**: Direct audio callback processing without intermediate queues
4. **Smart interruption**: Immediate buffer clearing on user speech detection

## Tool Integration

The system supports function calling through MCP (Model Context Protocol):
- Tools registered during session creation
- Function call requests handled via `FunctionCallRequest` event
- Results sent back via `SendFunctionCallResult` command

## Security Considerations

1. **API Key Management**: Stored securely in provider configuration
2. **WebSocket Security**: TLS encryption for all connections
3. **Audio Privacy**: Local processing, audio not stored unless explicitly saved
4. **Tool Permissions**: User approval required for function calls

## Future Enhancements

1. **Multi-modal support**: Image/video sharing in realtime
2. **Group conversations**: Multiple participants
3. **Audio effects**: Noise reduction, echo cancellation
4. **Custom models**: Support for self-hosted realtime endpoints
5. **Recording/playback**: Save and replay conversations

## Summary

Moly's OpenAI Realtime implementation provides a complete, production-ready voice conversation system with:
- Robust WebSocket communication
- Efficient audio processing pipeline
- Sophisticated interruption handling
- Clean separation of concerns (UI, protocol, client)
- Extensible architecture for multiple providers

The architecture emphasizes real-time performance, user experience, and maintainability through clear layer separation and event-driven design.