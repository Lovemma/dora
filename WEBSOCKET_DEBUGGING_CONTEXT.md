# Dora-OpenAI-WebSocket Debugging Context

## Overview
This document provides comprehensive debugging context for the `dora-openai-websocket` server, particularly focusing on dataflow connection issues encountered on Windows machines.

## Problem Summary
The WebSocket server fails to connect as a dynamic node to the Dora dataflow, resulting in the error:
```
WARNING: Dora node initialization timed out or panicked for 'server-XXXXX'
Continuing without Dora node connection - audio forwarding will not work
```

## Architecture Understanding

### How It Should Work
1. **Moly client** connects to WebSocket server via WebSocket protocol
2. **WebSocket server** receives session configuration from Moly
3. **Server creates a dataflow YAML** from template with unique node_id
4. **Server starts dataflow** using `dora start` command
5. **Server connects as dynamic node** to the running dataflow
6. **Audio/text flows** between Moly ↔ WebSocket ↔ Dataflow nodes (ASR, TTS, LLM)

### The Dynamic Node Problem
- The WebSocket server itself IS a dynamic node in the dataflow
- It needs to connect to the dataflow AFTER starting it
- This requires the Dora daemon to be running and accessible
- The node_id must match between the YAML file and the connection attempt

## Critical Code Sections

### 1. Dataflow Creation (main.rs:346-392)
```rust
// Generate unique ID for this connection
let id = random::<u16>();
let node_id = format!("server-{}", id);
let dataflow = format!("{}-{}.yml", input_audio_transcription, id);

// Create dataflow file from template
replace_placeholder_in_file(&template, &replacements, &dataflow).unwrap();
```

### 2. Dataflow Starting (main.rs:434-451)
```rust
// Start the dataflow using dora CLI
let output = std::process::Command::new("dora")
    .arg("start")
    .arg(&dataflow)
    .arg("--name")
    .arg(&node_id)
    .arg("--detach")
    .output()
    .expect("Failed to execute dora start command");
```

### 3. Node Initialization (main.rs:456-468)
```rust
// Wait for dataflow to initialize
tokio::time::sleep(tokio::time::Duration::from_millis(2000)).await;

// Try to initialize as dynamic node
let node_init_handle = tokio::task::spawn_blocking(move || {
    DoraNode::init_from_node_id(NodeId::from(node_id_clone))
});

// Timeout after 5 seconds
let (mut node, mut events) = match tokio::time::timeout(
    std::time::Duration::from_secs(5),
    node_init_handle
).await {
    Ok(Ok(Ok((n, e)))) => {
        println!("Dora node initialized successfully");
        (n, e)
    },
    _ => {
        println!("WARNING: Failed to initialize Dora node");
        // Continue without node connection
    }
}
```

## Debugging Steps for Windows

### 1. Verify Dora Installation
```powershell
# Check if dora CLI is available
dora --version

# Check if daemon is running
dora daemon status

# If not running, start it
dora daemon start
```

### 2. Check Template Files
The server looks for template files in the current directory:
- `whisper-template-metal.yml` (for macOS)
- `whisper-template.yml` (generic)
- Any file matching `*template*.yml`

Verify template exists and has correct structure:
```yaml
nodes:
  - id: NODE_ID  # This gets replaced with server-XXXXX
    build: cargo build --release -p dora-openai-websocket
    path: dynamic  # Critical: must be "dynamic"
    inputs:
      audio: primespeech/audio
      text: asr/transcription
    outputs:
      - audio
      - text
```

### 3. Debug Environment Variables
```powershell
# Set debug logging
$env:RUST_LOG="debug"
$env:DORA_LOG="debug"

# Check if custom coordinator address is needed
$env:DORA_COORDINATOR_ADDR="127.0.0.1:6832"
```

### 4. Manual Testing Steps

#### Step 1: Test Dataflow Creation
```powershell
# Create a test dataflow manually
Copy-Item whisper-template.yml test-dataflow.yml
(Get-Content test-dataflow.yml) -replace 'NODE_ID', 'test-node' | Set-Content test-dataflow.yml

# Try to start it
dora start test-dataflow.yml --name test-node
```

#### Step 2: Check Running Dataflows
```powershell
# List all running dataflows
dora list

# Check specific dataflow status
dora graph test-dataflow.yml
```

#### Step 3: Test Dynamic Node Connection
Create a minimal test program (`test_dynamic_node.rs`):
```rust
use dora_node_api::{DoraNode, NodeId};

fn main() {
    println!("Attempting to connect as dynamic node...");
    match DoraNode::init_from_node_id(NodeId::from("test-node")) {
        Ok((node, events)) => {
            println!("✓ Connected successfully!");
        }
        Err(e) => {
            println!("✗ Failed to connect: {:?}", e);
        }
    }
}
```

### 5. Common Windows-Specific Issues

#### Issue 1: Path Separators
Windows uses backslashes, which might cause issues:
```rust
// Original (might fail on Windows)
let template = format!("{}-template-metal.yml", input_audio_transcription);

// Windows-safe version
let template = format!("{}-template-metal.yml", input_audio_transcription)
    .replace("/", "\\");
```

#### Issue 2: Process Execution
Windows command execution might differ:
```rust
// Add explicit shell on Windows
let output = if cfg!(target_os = "windows") {
    std::process::Command::new("cmd")
        .args(&["/C", "dora", "start", &dataflow, "--name", &node_id, "--detach"])
        .output()
} else {
    std::process::Command::new("dora")
        .args(&["start", &dataflow, "--name", &node_id, "--detach"])
        .output()
};
```

#### Issue 3: Daemon Communication
Windows firewall might block daemon communication:
1. Check Windows Firewall settings
2. Add exception for Dora daemon (usually port 6832)
3. Try running with admin privileges

#### Issue 4: Timing Issues
Windows might need longer timeouts:
```rust
// Increase wait time for Windows
let wait_time = if cfg!(target_os = "windows") {
    tokio::time::Duration::from_millis(5000)  // 5 seconds
} else {
    tokio::time::Duration::from_millis(2000)  // 2 seconds
};
tokio::time::sleep(wait_time).await;
```

### 6. Diagnostic Logging to Add

Add these debug prints to `main.rs`:
```rust
// Before starting dataflow
println!("DEBUG: Current directory: {:?}", std::env::current_dir());
println!("DEBUG: Template file exists: {}", std::path::Path::new(&template).exists());
println!("DEBUG: Dataflow will be created at: {}", dataflow);

// After starting dataflow
println!("DEBUG: Dora start exit code: {}", output.status.code().unwrap_or(-1));
println!("DEBUG: Dora start stdout: {}", String::from_utf8_lossy(&output.stdout));
println!("DEBUG: Dora start stderr: {}", String::from_utf8_lossy(&output.stderr));

// Before node init
println!("DEBUG: Attempting to connect with node_id: {}", node_id);
println!("DEBUG: DORA_COORDINATOR_ADDR: {:?}", std::env::var("DORA_COORDINATOR_ADDR"));

// After node init attempt
if let Err(e) = DoraNode::init_from_node_id(NodeId::from(node_id)) {
    println!("DEBUG: Node init error details: {:?}", e);
    println!("DEBUG: Error source: {:?}", e.source());
}
```

### 7. Alternative Approaches Tried

#### Approach 1: Dataflow Persistence (Failed)
- Tried to keep dataflows running between connections
- Issue: Dynamic nodes can't reconnect with new IDs
- Conclusion: Not feasible with current architecture

#### Approach 2: Fixed Node IDs (Failed)
- Tried using same node_id across reconnections
- Issue: Node cleanup on disconnect prevents reuse
- Conclusion: Each connection needs unique ID

#### Approach 3: External Dataflow Management (Not Implemented)
- Idea: Separate WebSocket server from dataflow
- WebSocket acts as proxy, not as node
- Would require significant architecture change

### 8. Working Configuration (macOS)

For reference, here's what works on macOS:
```yaml
# Environment
RUST_LOG=info
No special DORA_COORDINATOR_ADDR needed

# Timeouts
Dataflow init wait: 2000ms
Node init timeout: 5000ms

# Template location
./whisper-template-metal.yml (in same directory as server)
```

### 9. Recommended Windows Debug Sequence

1. **Start fresh**
   ```powershell
   dora daemon stop
   dora destroy --all
   dora daemon start
   ```

2. **Run with maximum logging**
   ```powershell
   $env:RUST_LOG="debug"
   $env:RUST_BACKTRACE="full"
   cargo run --release -p dora-openai-websocket
   ```

3. **In another terminal, monitor daemon**
   ```powershell
   dora daemon status
   dora list --watch
   ```

4. **Connect with Moly and observe**
   - Note exact error messages
   - Check if dataflow appears in `dora list`
   - Check if node_id matches between logs

### 10. Critical Questions for Windows Debugging

1. Does `dora daemon status` show daemon running?
2. Can you manually start a dataflow with `dora start`?
3. Does the template file exist in the working directory?
4. Are there any Windows Firewall warnings?
5. Does running as Administrator help?
6. What's the exact error message in node initialization?
7. Does `dora list` show the dataflow after "Dataflow started successfully"?
8. Can you connect to the coordinator at 127.0.0.1:6832?

## Related Files to Check

1. **Template file**: Must exist and have correct structure
2. **Cargo.toml**: Ensure dora-node-api version matches daemon
3. **dora-daemon logs**: Usually in `~/.dora/daemon.log`
4. **Windows Event Viewer**: Check for system-level errors

## Contact Points

- Original working version: `/Users/yuechen/home/mcp/dora/node-hub/dora-openai-websocket/`
- Current version: `/Users/yuechen/home/fresh/dora/node-hub/dora-openai-websocket/`
- Key difference: Increased timeouts, better error handling

This debugging context should help identify why the dynamic node connection fails on Windows.