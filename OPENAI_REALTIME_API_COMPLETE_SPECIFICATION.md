# OpenAI Realtime API Complete Specification

## Overview
The OpenAI Realtime API enables real-time, low-latency, multimodal conversational experiences. It uses WebSocket connections for bidirectional audio streaming and supports both audio and text modalities with function calling capabilities.

## Connection Details

### WebSocket Endpoint
```
wss://api.openai.com/v1/realtime?model=gpt-4o-realtime-preview-2024-10-01
```

### Authentication
```
Authorization: Bearer YOUR_API_KEY
OpenAI-Beta: realtime=v1
```

## Complete Event Specification

### Client Events (Client → Server)

#### 1. Session Management Events

##### `session.update`
**Purpose**: Update the session configuration
**When to use**: To modify voice, instructions, tools, or other session parameters
```json
{
  "type": "session.update",
  "session": {
    "modalities": ["text", "audio"],
    "instructions": "You are a helpful assistant",
    "voice": "alloy",
    "input_audio_format": "pcm16",
    "output_audio_format": "pcm16",
    "input_audio_transcription": {
      "model": "whisper-1"
    },
    "turn_detection": {
      "type": "server_vad",
      "threshold": 0.5,
      "prefix_padding_ms": 300,
      "silence_duration_ms": 200
    },
    "tools": [...],
    "tool_choice": "auto",
    "temperature": 0.8,
    "max_response_output_tokens": 4096
  }
}
```

#### 2. Input Audio Events

##### `input_audio_buffer.append`
**Purpose**: Stream audio from the user to the server
**Format**: Base64-encoded PCM16 audio chunks
```json
{
  "type": "input_audio_buffer.append",
  "audio": "base64_encoded_audio_data"
}
```

##### `input_audio_buffer.commit`
**Purpose**: Commit the current audio buffer for processing
**When to use**: When user stops speaking or to force processing
```json
{
  "type": "input_audio_buffer.commit"
}
```

##### `input_audio_buffer.clear`
**Purpose**: Clear the current audio buffer
**When to use**: To cancel current input or reset
```json
{
  "type": "input_audio_buffer.clear"
}
```

#### 3. Response Management Events

##### `response.create`
**Purpose**: Generate a response from the model
**When to use**: To trigger AI response programmatically
```json
{
  "type": "response.create",
  "response": {
    "modalities": ["text", "audio"],
    "instructions": "Please be brief",
    "voice": "alloy",
    "output_audio_format": "pcm16",
    "tools": [...],
    "tool_choice": "auto",
    "temperature": 0.7,
    "max_output_tokens": 200
  }
}
```

##### `response.cancel`
**Purpose**: Cancel an in-progress response
**When to use**: To interrupt the AI mid-response
```json
{
  "type": "response.cancel"
}
```

#### 4. Conversation Management Events

##### `conversation.item.create`
**Purpose**: Add an item to the conversation
**Use cases**: Add user messages, assistant messages, function calls, or function results
```json
{
  "type": "conversation.item.create",
  "item": {
    "type": "message",
    "role": "user",
    "content": [
      {
        "type": "input_text",
        "text": "Hello, how are you?"
      }
    ]
  }
}
```

**Function Call Output Example**:
```json
{
  "type": "conversation.item.create",
  "item": {
    "type": "function_call_output",
    "call_id": "call_abc123",
    "output": "{"temperature": 72, "conditions": "sunny"}"
  }
}
```

##### `conversation.item.truncate`
**Purpose**: Truncate an existing conversation item
**When to use**: To cut off audio or text at a specific point
```json
{
  "type": "conversation.item.truncate",
  "item_id": "item_abc123",
  "content_index": 0,
  "audio_end_ms": 1500
}
```

##### `conversation.item.delete`
**Purpose**: Remove an item from conversation history
**When to use**: To manage context or correct mistakes
```json
{
  "type": "conversation.item.delete",
  "item_id": "item_abc123"
}
```

### Server Events (Server → Client)

#### 1. Session Events

##### `session.created`
**Purpose**: Confirms session creation
**When received**: After WebSocket connection established
```json
{
  "type": "session.created",
  "session": {
    "id": "session_abc123",
    "object": "realtime.session",
    "model": "gpt-4o-realtime-preview-2024-10-01",
    "modalities": ["text", "audio"],
    "instructions": "...",
    "voice": "alloy",
    "turn_detection": {...},
    "tools": [...],
    ...
  }
}
```

##### `session.updated`
**Purpose**: Confirms session configuration update
**When received**: After successful `session.update`
```json
{
  "type": "session.updated",
  "session": {...}
}
```

#### 2. Input Audio Events

##### `input_audio_buffer.committed`
**Purpose**: Confirms audio buffer was committed
**When received**: After `input_audio_buffer.commit`
```json
{
  "type": "input_audio_buffer.committed",
  "item_id": "item_abc123"
}
```

##### `input_audio_buffer.cleared`
**Purpose**: Confirms audio buffer was cleared
**When received**: After `input_audio_buffer.clear`
```json
{
  "type": "input_audio_buffer.cleared"
}
```

##### `input_audio_buffer.speech_started`
**Purpose**: Indicates user started speaking
**When received**: When VAD detects speech
```json
{
  "type": "input_audio_buffer.speech_started",
  "audio_start_ms": 1000,
  "item_id": "item_abc123"
}
```

##### `input_audio_buffer.speech_stopped`
**Purpose**: Indicates user stopped speaking
**When received**: When VAD detects silence
```json
{
  "type": "input_audio_buffer.speech_stopped",
  "audio_end_ms": 3500,
  "item_id": "item_abc123"
}
```

#### 3. Response Events

##### `response.created`
**Purpose**: Response generation started
**When received**: When model begins generating
```json
{
  "type": "response.created",
  "response": {
    "id": "resp_abc123",
    "object": "realtime.response",
    "status": "in_progress",
    "output": [],
    "usage": null
  }
}
```

##### `response.done`
**Purpose**: Response generation completed
**When received**: When model finishes response
```json
{
  "type": "response.done",
  "response": {
    "id": "resp_abc123",
    "object": "realtime.response",
    "status": "completed",
    "output": [...],
    "usage": {
      "total_tokens": 500,
      "input_tokens": 100,
      "output_tokens": 400
    }
  }
}
```

##### `response.cancelled`
**Purpose**: Response was cancelled
**When received**: After `response.cancel` or interruption
```json
{
  "type": "response.cancelled",
  "response": {
    "id": "resp_abc123",
    "object": "realtime.response",
    "status": "cancelled"
  }
}
```

##### `response.output_item.added`
**Purpose**: New output item added to response
**When received**: When response includes new content
```json
{
  "type": "response.output_item.added",
  "response_id": "resp_abc123",
  "output_index": 0,
  "item": {
    "id": "item_def456",
    "object": "realtime.item",
    "type": "message",
    "role": "assistant"
  }
}
```

##### `response.output_item.done`
**Purpose**: Output item is complete
**When received**: When an output item finishes
```json
{
  "type": "response.output_item.done",
  "response_id": "resp_abc123",
  "output_index": 0,
  "item": {...}
}
```

##### `response.content_part.added`
**Purpose**: New content part added to item
**When received**: Start of text/audio content
```json
{
  "type": "response.content_part.added",
  "response_id": "resp_abc123",
  "item_id": "item_def456",
  "output_index": 0,
  "content_index": 0,
  "part": {
    "type": "audio",
    "transcript": null
  }
}
```

##### `response.content_part.done`
**Purpose**: Content part is complete
**When received**: End of text/audio segment
```json
{
  "type": "response.content_part.done",
  "response_id": "resp_abc123",
  "item_id": "item_def456",
  "output_index": 0,
  "content_index": 0,
  "part": {...}
}
```

#### 4. Delta Events (Streaming)

##### `response.audio.delta`
**Purpose**: Stream audio output
**Format**: Base64-encoded PCM16 audio chunks
```json
{
  "type": "response.audio.delta",
  "response_id": "resp_abc123",
  "item_id": "item_def456",
  "output_index": 0,
  "content_index": 0,
  "delta": "base64_encoded_audio"
}
```

##### `response.audio.done`
**Purpose**: Audio streaming complete
```json
{
  "type": "response.audio.done",
  "response_id": "resp_abc123",
  "item_id": "item_def456",
  "output_index": 0,
  "content_index": 0
}
```

##### `response.audio_transcript.delta`
**Purpose**: Stream transcript of audio output
```json
{
  "type": "response.audio_transcript.delta",
  "response_id": "resp_abc123",
  "item_id": "item_def456",
  "output_index": 0,
  "content_index": 0,
  "delta": "Hello, "
}
```

##### `response.audio_transcript.done`
**Purpose**: Audio transcript complete
```json
{
  "type": "response.audio_transcript.done",
  "response_id": "resp_abc123",
  "item_id": "item_def456",
  "output_index": 0,
  "content_index": 0,
  "transcript": "Hello, how can I help you today?"
}
```

##### `response.text.delta`
**Purpose**: Stream text output
```json
{
  "type": "response.text.delta",
  "response_id": "resp_abc123",
  "item_id": "item_def456",
  "output_index": 0,
  "content_index": 0,
  "delta": "Sure, I can help "
}
```

##### `response.text.done`
**Purpose**: Text streaming complete
```json
{
  "type": "response.text.done",
  "response_id": "resp_abc123",
  "item_id": "item_def456",
  "output_index": 0,
  "content_index": 0,
  "text": "Sure, I can help with that."
}
```

#### 5. Function Calling Events

##### `response.function_call_arguments.delta`
**Purpose**: Stream function call arguments
```json
{
  "type": "response.function_call_arguments.delta",
  "response_id": "resp_abc123",
  "item_id": "item_def456",
  "output_index": 0,
  "call_id": "call_xyz789",
  "delta": "{\"location\": \"San "
}
```

##### `response.function_call_arguments.done`
**Purpose**: Function call arguments complete
```json
{
  "type": "response.function_call_arguments.done",
  "response_id": "resp_abc123",
  "item_id": "item_def456",
  "output_index": 0,
  "call_id": "call_xyz789",
  "name": "get_weather",
  "arguments": "{\"location\": \"San Francisco\", \"unit\": \"celsius\"}"
}
```

#### 6. Conversation Events

##### `conversation.created`
**Purpose**: New conversation started
```json
{
  "type": "conversation.created",
  "conversation": {
    "id": "conv_abc123",
    "object": "realtime.conversation"
  }
}
```

##### `conversation.item.created`
**Purpose**: Item added to conversation
```json
{
  "type": "conversation.item.created",
  "item": {
    "id": "item_abc123",
    "object": "realtime.item",
    "type": "message",
    "status": "completed",
    "role": "user",
    "content": [...]
  }
}
```

##### `conversation.item.deleted`
**Purpose**: Item removed from conversation
```json
{
  "type": "conversation.item.deleted",
  "item_id": "item_abc123"
}
```

##### `conversation.item.truncated`
**Purpose**: Item was truncated
```json
{
  "type": "conversation.item.truncated",
  "item_id": "item_abc123",
  "content_index": 0,
  "audio_end_ms": 1500
}
```

##### `conversation.item.input_audio_transcription.completed`
**Purpose**: User audio transcribed successfully
```json
{
  "type": "conversation.item.input_audio_transcription.completed",
  "item_id": "item_abc123",
  "content_index": 0,
  "transcript": "Hello, how are you?"
}
```

##### `conversation.item.input_audio_transcription.failed`
**Purpose**: Transcription failed
```json
{
  "type": "conversation.item.input_audio_transcription.failed",
  "item_id": "item_abc123",
  "content_index": 0,
  "error": {
    "type": "transcription_error",
    "message": "Audio quality too poor"
  }
}
```

#### 7. Rate Limit Events

##### `rate_limits.updated`
**Purpose**: Rate limit information updated
```json
{
  "type": "rate_limits.updated",
  "rate_limits": [
    {
      "name": "requests",
      "limit": 100,
      "remaining": 95,
      "reset_seconds": 60
    },
    {
      "name": "tokens",
      "limit": 50000,
      "remaining": 45000,
      "reset_seconds": 60
    }
  ]
}
```

#### 8. Error Events

##### `error`
**Purpose**: Error occurred
```json
{
  "type": "error",
  "error": {
    "type": "invalid_request_error",
    "code": "invalid_audio_format",
    "message": "Audio must be base64-encoded PCM16",
    "param": "audio",
    "event_id": "event_abc123"
  }
}
```

## Configuration Parameters

### Session Configuration

| Parameter | Type | Options | Description |
|-----------|------|---------|-------------|
| **modalities** | array | ["text"], ["audio"], ["text", "audio"] | Input/output modalities |
| **instructions** | string | Any text | System prompt for the model |
| **voice** | string | alloy, echo, fable, onyx, nova, shimmer | TTS voice selection |
| **input_audio_format** | string | pcm16, g711_ulaw, g711_alaw | Input audio encoding |
| **output_audio_format** | string | pcm16, g711_ulaw, g711_alaw | Output audio encoding |
| **input_audio_transcription** | object | {model: "whisper-1"} | Transcription settings |
| **turn_detection** | object | See below | VAD configuration |
| **tools** | array | Tool definitions | Available functions |
| **tool_choice** | string | none, auto, required, {function: name} | Tool selection strategy |
| **temperature** | float | 0.6 - 1.2 | Response randomness |
| **max_response_output_tokens** | int | Up to 4096 | Max tokens in response |

### Turn Detection (VAD) Configuration

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| **type** | string | server_vad | VAD type (server_vad or none) |
| **threshold** | float | 0.5 | Speech detection sensitivity (0.0-1.0) |
| **prefix_padding_ms** | int | 300 | Audio included before speech |
| **silence_duration_ms** | int | 500 | Silence duration to end turn |
| **create_response** | bool | true | Auto-respond after speech |

### Audio Formats

| Format | Sample Rate | Bit Depth | Channels | Description |
|--------|------------|-----------|----------|-------------|
| **pcm16** | 24000 Hz | 16-bit | 1 (mono) | Linear PCM, little-endian |
| **g711_ulaw** | 8000 Hz | 8-bit | 1 (mono) | μ-law compression |
| **g711_alaw** | 8000 Hz | 8-bit | 1 (mono) | A-law compression |

### Tool Definition Format

```json
{
  "type": "function",
  "name": "get_weather",
  "description": "Get current weather for a location",
  "parameters": {
    "type": "object",
    "properties": {
      "location": {
        "type": "string",
        "description": "City and state, e.g. San Francisco, CA"
      },
      "unit": {
        "type": "string",
        "enum": ["celsius", "fahrenheit"],
        "description": "Temperature unit"
      }
    },
    "required": ["location"]
  }
}
```

## Conversation Item Types

### Message Item
```json
{
  "type": "message",
  "role": "user" | "assistant" | "system",
  "content": [
    {
      "type": "input_text" | "text",
      "text": "Message content"
    },
    {
      "type": "input_audio" | "audio",
      "audio": "base64_encoded_audio",
      "transcript": "Optional transcript"
    }
  ]
}
```

### Function Call Item
```json
{
  "type": "function_call",
  "name": "function_name",
  "call_id": "call_abc123",
  "arguments": "JSON string of arguments"
}
```

### Function Call Output Item
```json
{
  "type": "function_call_output",
  "call_id": "call_abc123",
  "output": "Function result as string"
}
```

## Rate Limits

| Limit Type | Tier 1 | Tier 2 | Tier 3 | Tier 4 | Tier 5 |
|------------|--------|--------|--------|--------|--------|
| **RPM** (audio) | 100 | 200 | 500 | 1000 | 1000 |
| **TPM** (audio) | 20,000 | 40,000 | 80,000 | 160,000 | 320,000 |

## Best Practices

### 1. Connection Management
- Implement exponential backoff for reconnection
- Handle WebSocket close events gracefully
- Monitor connection health with ping/pong

### 2. Audio Streaming
- Use consistent chunk sizes (e.g., 20ms of audio)
- Buffer audio on client side for smooth playback
- Handle network jitter with adaptive buffering

### 3. Error Handling
- Implement retry logic for transient errors
- Log all errors for debugging
- Provide user feedback for failures

### 4. Performance Optimization
- Use server VAD to reduce latency
- Stream audio in real-time, don't batch
- Minimize message size with efficient encoding

### 5. Context Management
- Truncate old conversation items to stay within limits
- Use conversation.item.delete for irrelevant context
- Monitor token usage via rate_limits events

## Common Integration Patterns

### 1. Basic Voice Conversation
```
1. Connect WebSocket
2. Configure session with voice and VAD
3. Stream user audio via input_audio_buffer.append
4. Receive AI audio via response.audio.delta
5. Play audio to user
```

### 2. Function-Enabled Assistant
```
1. Register tools in session configuration
2. Stream user request
3. Receive function_call_arguments.done
4. Execute function locally
5. Send result via conversation.item.create
6. Receive final response with function result context
```

### 3. Interruption Handling
```
1. Detect user speech during AI response
2. Send response.cancel
3. Clear output audio buffer
4. Process new user input
```

### 4. Multi-Turn Conversation
```
1. Maintain conversation history
2. Use server VAD for automatic turn-taking
3. Handle speech_started/stopped events
4. Manage context with item truncation
```

## Error Types

| Error Type | Code | Description | Recovery |
|------------|------|-------------|----------|
| **invalid_request_error** | Various | Malformed request | Fix request format |
| **authentication_error** | invalid_api_key | Bad credentials | Check API key |
| **rate_limit_error** | rate_limit_exceeded | Too many requests | Implement backoff |
| **server_error** | internal_error | Server issue | Retry with backoff |
| **connection_error** | websocket_error | Connection lost | Reconnect |

## Compliance Checklist

- [ ] Handle all server events
- [ ] Implement proper audio encoding/decoding
- [ ] Support function calling protocol
- [ ] Manage conversation state
- [ ] Handle errors gracefully
- [ ] Implement rate limit tracking
- [ ] Support all audio formats
- [ ] Handle VAD events
- [ ] Manage response lifecycle
- [ ] Support interruptions
- [ ] Implement reconnection logic
- [ ] Track token usage
- [ ] Support all voice options
- [ ] Handle transcription events
- [ ] Implement proper cleanup

This specification provides complete coverage of the OpenAI Realtime API, enabling full implementation of a compliant client or server.