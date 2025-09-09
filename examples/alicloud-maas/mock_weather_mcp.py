#!/usr/bin/env python3
"""
Mock Weather MCP Server for testing Alibaba Cloud MCP integration.
Implements the Model Context Protocol (MCP) for weather queries.
"""

import json
import sys
import logging
from typing import Dict, Any, List

# Configure logging
logging.basicConfig(
    level=logging.DEBUG, 
    format='%(asctime)s - %(levelname)s - %(message)s',
    filename='/tmp/weather_mcp.log',
    filemode='a'
)

# Mock weather data for Chinese cities
WEATHER_DATA = {
    "beijing": {
        "temperature": 15,
        "condition": "Partly Cloudy",
        "humidity": 45,
        "wind_speed": 12,
        "description": "Beijing weather: 15°C, partly cloudy with moderate humidity"
    },
    "shanghai": {
        "temperature": 22,
        "condition": "Sunny",
        "humidity": 60,
        "wind_speed": 8,
        "description": "Shanghai weather: 22°C, sunny with high humidity"
    },
    "shenzhen": {
        "temperature": 28,
        "condition": "Humid",
        "humidity": 75,
        "wind_speed": 5,
        "description": "Shenzhen weather: 28°C, humid with light winds"
    },
    "guangzhou": {
        "temperature": 26,
        "condition": "Rainy",
        "humidity": 80,
        "wind_speed": 10,
        "description": "Guangzhou weather: 26°C, rainy with high humidity"
    },
    "北京": {  # Chinese name support
        "temperature": 15,
        "condition": "多云",
        "humidity": 45,
        "wind_speed": 12,
        "description": "北京天气：15°C，多云，湿度适中"
    },
    "上海": {
        "temperature": 22,
        "condition": "晴天",
        "humidity": 60,
        "wind_speed": 8,
        "description": "上海天气：22°C，晴天，湿度较高"
    }
}

def handle_initialize(request_id: int, params: Dict[str, Any]) -> Dict[str, Any]:
    """Handle initialization request."""
    logging.info("Initializing Mock Weather MCP Server")
    return {
        "jsonrpc": "2.0",
        "id": request_id,
        "result": {
            "protocolVersion": "0.1.0",
            "capabilities": {
                "tools": {}
            },
            "serverInfo": {
                "name": "mock-weather",
                "version": "1.0.0"
            }
        }
    }

def handle_tools_list(request_id: int) -> Dict[str, Any]:
    """Return the list of available tools."""
    logging.info("Listing available tools")
    return {
        "jsonrpc": "2.0",
        "id": request_id,
        "result": {
            "tools": [
                {
                    "name": "get_weather",
                    "description": "Get current weather for a city. Supports major Chinese cities.",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "city": {
                                "type": "string",
                                "description": "City name (e.g., 'beijing', 'shanghai', '北京', '上海')"
                            }
                        },
                        "required": ["city"]
                    }
                },
                {
                    "name": "list_cities",
                    "description": "List all cities with available weather data",
                    "inputSchema": {
                        "type": "object",
                        "properties": {}
                    }
                }
            ]
        }
    }

def handle_tools_call(request_id: int, params: Dict[str, Any]) -> Dict[str, Any]:
    """Handle tool execution requests."""
    tool_name = params.get("name")
    arguments = params.get("arguments", {})
    
    logging.info(f"Executing tool: {tool_name} with arguments: {arguments}")
    
    if tool_name == "get_weather":
        city = arguments.get("city", "").lower()
        
        # Check both English and Chinese names
        if city in WEATHER_DATA:
            weather = WEATHER_DATA[city]
            result = {
                "city": city,
                "temperature": weather["temperature"],
                "condition": weather["condition"],
                "humidity": weather["humidity"],
                "wind_speed": weather["wind_speed"],
                "description": weather["description"]
            }
            logging.info(f"Weather data found for {city}: {result}")
        else:
            result = {
                "error": f"Weather data not available for city: {city}",
                "available_cities": list(WEATHER_DATA.keys())
            }
            logging.warning(f"City not found: {city}")
            
    elif tool_name == "list_cities":
        result = {
            "cities": list(WEATHER_DATA.keys()),
            "total": len(WEATHER_DATA)
        }
        logging.info(f"Listed {len(WEATHER_DATA)} cities")
    else:
        result = {"error": f"Unknown tool: {tool_name}"}
        logging.error(f"Unknown tool requested: {tool_name}")
    
    return {
        "jsonrpc": "2.0",
        "id": request_id,
        "result": {
            "content": [
                {
                    "type": "text",
                    "text": json.dumps(result, ensure_ascii=False, indent=2)
                }
            ]
        }
    }

def handle_request(request: Dict[str, Any]) -> Dict[str, Any]:
    """Route requests to appropriate handlers."""
    method = request.get("method")
    request_id = request.get("id")
    params = request.get("params", {})
    
    logging.debug(f"Received request: {method}")
    
    if method == "initialize":
        return handle_initialize(request_id, params)
    elif method == "tools/list":
        return handle_tools_list(request_id)
    elif method == "tools/call":
        return handle_tools_call(request_id, params)
    else:
        logging.error(f"Unknown method: {method}")
        return {
            "jsonrpc": "2.0",
            "id": request_id,
            "error": {
                "code": -32601,
                "message": f"Method not found: {method}"
            }
        }

def main():
    """Main MCP server loop."""
    logging.info("Mock Weather MCP Server started")
    print("Mock Weather MCP Server ready", file=sys.stderr)
    
    while True:
        try:
            # Read line from stdin
            line = sys.stdin.readline()
            if not line:
                logging.info("EOF received, shutting down")
                break
                
            line = line.strip()
            if not line:
                continue
                
            # Parse JSON-RPC request
            try:
                request = json.loads(line)
                logging.debug(f"Parsed request: {request}")
            except json.JSONDecodeError as e:
                logging.error(f"Failed to parse JSON: {e}")
                continue
            
            # Handle request
            response = handle_request(request)
            
            # Send response
            response_json = json.dumps(response, ensure_ascii=False)
            print(response_json)
            sys.stdout.flush()
            logging.debug(f"Sent response: {response_json}")
            
        except KeyboardInterrupt:
            logging.info("Interrupted, shutting down")
            break
        except Exception as e:
            logging.error(f"Unexpected error: {e}", exc_info=True)
            # Send error response
            error_response = {
                "jsonrpc": "2.0",
                "id": request.get("id") if 'request' in locals() else None,
                "error": {
                    "code": -32603,
                    "message": f"Internal error: {str(e)}"
                }
            }
            print(json.dumps(error_response))
            sys.stdout.flush()
    
    logging.info("Mock Weather MCP Server stopped")

if __name__ == "__main__":
    main()