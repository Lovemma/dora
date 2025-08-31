use std::collections::HashMap;

use dora_node_api::{
    DoraNode, Event, Parameter,
    arrow::array::{AsArray, StringArray},
    dora_core::config::DataId,
};
use eyre::{Context, Result};
use async_openai::{
    Client,
    types::{
        ChatCompletionRequestMessage, ChatCompletionRequestUserMessage,
        ChatCompletionRequestAssistantMessage, ChatCompletionRequestSystemMessage,
        CreateChatCompletionRequestArgs, Role,
    },
};
use futures::StreamExt;
use serde_json::json;

mod config;
use config::Config;

// Helper function to send log messages
fn send_log(node: &mut DoraNode, level: &str, message: &str) -> Result<()> {
    let log_data = json!({
        "node": "maas-client",
        "level": level,
        "message": message,
        "timestamp": chrono::Utc::now().timestamp()
    });
    node.send_output(
        DataId::from("log".to_string()),
        Default::default(),
        StringArray::from(vec![log_data.to_string().as_str()]),
    ).context("Failed to send log output")?;
    Ok(())
}

struct ChatSession {
    messages: Vec<ChatCompletionRequestMessage>,
    total_tokens: usize,
}

impl ChatSession {
    fn new(system_prompt: String) -> Self {
        let system_message = ChatCompletionRequestSystemMessage {
            content: Some(system_prompt),
            name: None,
            tool_calls: None,
        };
        
        Self {
            messages: vec![ChatCompletionRequestMessage::System(system_message)],
            total_tokens: 0,
        }
    }

    fn add_user_message(&mut self, content: String) {
        let message = ChatCompletionRequestUserMessage {
            content: Some(async_openai::types::ChatCompletionRequestUserMessageContent::Text(content)),
            name: None,
            tool_calls: None,
        };
        self.messages.push(ChatCompletionRequestMessage::User(message));
    }

    fn add_assistant_message(&mut self, content: String) {
        let message = ChatCompletionRequestAssistantMessage {
            content: Some(content),
            name: None,
            tool_calls: None,
            function_call: None,
            weight: None,
            refusal: None,
            audio: None,
        };
        self.messages.push(ChatCompletionRequestMessage::Assistant(message));
    }

    fn manage_history(&mut self, max_exchanges: usize) {
        // Keep system message + last N exchanges (N*2 messages)
        let max_messages = 1 + (max_exchanges * 2);
        if self.messages.len() > max_messages {
            let excess = self.messages.len() - max_messages;
            // Remove old messages but keep system prompt
            self.messages.drain(1..=excess);
        }
    }

    fn reset(&mut self) {
        // Keep only system message
        self.messages.truncate(1);
        self.total_tokens = 0;
    }
}

#[tokio::main]
async fn main() -> Result<()> {
    // Load configuration
    let config = Config::load().context("Failed to load configuration")?;
    
    // Initialize OpenAI client (uses OPENAI_API_KEY env var automatically)
    let client = Client::new();
    
    // Initialize Dora node
    let (mut node, events) = DoraNode::init_from_env()?;
    
    // Send initialization logs
    send_log(&mut node, "INFO", "MaaS Client initialized (streaming enabled)")?;
    send_log(&mut node, "INFO", &format!("Model: {}", config.default_model))?;
    
    // Session storage
    let mut sessions: HashMap<String, ChatSession> = HashMap::new();
    
    // Process events
    let events = futures::executor::block_on_stream(events);
    for event in events {
        match event {
            Event::Input { id, data, metadata } => {
                // Extract session ID from metadata
                let session_id = metadata.parameters.get("session_id")
                    .and_then(|p| match p {
                        Parameter::String(s) => Some(s.clone()),
                        _ => None,
                    })
                    .unwrap_or_else(|| "default".to_string());
                
                match id.as_str() {
                    "text" | "text_to_audio" => {
                        // Extract text from input
                        let text_array = data.as_string::<i32>();
                        let user_text = text_array.iter()
                            .filter_map(|s| s)
                            .collect::<Vec<_>>()
                            .join(" ");
                        
                        if user_text.is_empty() {
                            send_log(&mut node, "WARNING", "Received empty text input")?;
                            continue;
                        }
                        
                        send_log(&mut node, "INFO", &format!("Processing: {}", user_text))?;
                        
                        // Get or create session
                        let session = sessions.entry(session_id.clone())
                            .or_insert_with(|| ChatSession::new(config.system_prompt.clone()));
                        
                        // Add user message
                        session.add_user_message(user_text.clone());
                        
                        // Manage history
                        session.manage_history(config.max_history_exchanges);
                        
                        // Create streaming chat completion request
                        let request = CreateChatCompletionRequestArgs::default()
                            .model(&config.default_model)
                            .messages(session.messages.clone())
                            .temperature(0.7)
                            .max_tokens(256u32)
                            .build()?;
                        
                        // Stream the response
                        if config.enable_streaming.unwrap_or(true) {
                            send_log(&mut node, "DEBUG", "Starting streaming response")?;
                            
                            let mut stream = client.chat().create_stream(request).await?;
                            let mut accumulated_content = String::new();
                            let mut chunk_count = 0;
                            
                            while let Some(result) = stream.next().await {
                                match result {
                                    Ok(response) => {
                                        for choice in &response.choices {
                                            if let Some(ref content) = choice.delta.content {
                                                accumulated_content.push_str(content);
                                                chunk_count += 1;
                                                
                                                // Send each chunk as it arrives
                                                node.send_output(
                                                    DataId::from("text".to_string()),
                                                    Default::default(),
                                                    StringArray::from(vec![content.as_str()]),
                                                ).context("Failed to send text chunk")?;
                                                
                                                // Log every 10th chunk to avoid spam
                                                if chunk_count % 10 == 0 {
                                                    send_log(&mut node, "DEBUG", 
                                                        &format!("Streamed {} chunks", chunk_count))?;
                                                }
                                            }
                                        }
                                    }
                                    Err(e) => {
                                        send_log(&mut node, "ERROR", 
                                            &format!("Stream error: {}", e))?;
                                        break;
                                    }
                                }
                            }
                            
                            // Add complete message to session
                            if !accumulated_content.is_empty() {
                                session.add_assistant_message(accumulated_content.clone());
                                send_log(&mut node, "INFO", 
                                    &format!("Streamed response complete ({} chars, {} chunks)", 
                                        accumulated_content.len(), chunk_count))?;
                            }
                        } else {
                            // Non-streaming mode
                            let response = client.chat().create(request).await?;
                            
                            if let Some(choice) = response.choices.first() {
                                if let Some(ref content) = choice.message.content {
                                    session.add_assistant_message(content.clone());
                                    
                                    node.send_output(
                                        DataId::from("text".to_string()),
                                        Default::default(),
                                        StringArray::from(vec![content.as_str()]),
                                    ).context("Failed to send text output")?;
                                    
                                    send_log(&mut node, "INFO", 
                                        &format!("Generated response ({} chars)", content.len()))?;
                                }
                            }
                        }
                    }
                    "control" => {
                        // Handle control commands
                        let command_array = data.as_string::<i32>();
                        if let Some(command) = command_array.iter().next().flatten() {
                            send_log(&mut node, "DEBUG", &format!("Control command: {}", command))?;
                            
                            match command {
                                "reset" => {
                                    if let Some(session) = sessions.get_mut(&session_id) {
                                        session.reset();
                                        send_log(&mut node, "INFO", &format!("Reset session: {}", session_id))?;
                                    }
                                }
                                "ready" => {
                                    // Send ready status
                                    node.send_output(
                                        DataId::from("status".to_string()),
                                        Default::default(),
                                        StringArray::from(vec!["ready"]),
                                    ).context("Failed to send status output")?;
                                }
                                "exit" => {
                                    sessions.remove(&session_id);
                                    send_log(&mut node, "INFO", &format!("Removed session: {}", session_id))?;
                                }
                                _ => {
                                    send_log(&mut node, "WARNING", &format!("Unknown control command: {}", command))?;
                                }
                            }
                        }
                    }
                    _ => {
                        send_log(&mut node, "WARNING", &format!("Unknown input ID: {}", id))?;
                    }
                }
            }
            Event::Stop(_) => {
                send_log(&mut node, "INFO", "Received stop event, shutting down")?;
                break;
            }
            _ => {}
        }
    }
    
    send_log(&mut node, "INFO", "MaaS Client stopped")?;
    Ok(())
}