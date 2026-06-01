import sys
import json
from pathlib import Path

# Paths
BASE_DIR = Path(__file__).resolve().parent.parent
STITCH_DESIGN_PATH = BASE_DIR / "stitch_design.json"

def log(msg: str):
    """Write log messages to stderr so they don't corrupt stdout JSON-RPC stream."""
    sys.stderr.write(f"[StitchMCP] {msg}\n")
    sys.stderr.flush()

def handle_initialize(msg_id, params):
    return {
        "jsonrpc": "2.0",
        "id": msg_id,
        "result": {
            "protocolVersion": "2024-11-05",
            "capabilities": {
                "tools": {}
            },
            "serverInfo": {
                "name": "stitch-mcp",
                "version": "1.0.0"
            }
        }
    }

def handle_list_tools(msg_id):
    tools = [
        {
            "name": "get_stitch_tokens",
            "description": "Read the current active Google Stitch design tokens from stitch_design.json.",
            "inputSchema": {
                "type": "object",
                "properties": {}
            }
        },
        {
            "name": "update_stitch_tokens",
            "description": "Overwrite/update Google Stitch design tokens in stitch_design.json.",
            "inputSchema": {
                "type": "object",
                "properties": {
                    "tokens": {
                        "type": "object",
                        "description": "Full JSON object of tokens (e.g. primary_color, bg_color)."
                    }
                },
                "required": ["tokens"]
            }
        }
    ]
    return {
        "jsonrpc": "2.0",
        "id": msg_id,
        "result": {
            "tools": tools
        }
    }

def handle_call_tool(msg_id, params):
    name = params.get("name")
    arguments = params.get("arguments", {})
    
    if name == "get_stitch_tokens":
        try:
            if STITCH_DESIGN_PATH.exists():
                with open(STITCH_DESIGN_PATH, "r", encoding="utf-8") as f:
                    tokens = json.load(f)
            else:
                tokens = {}
            return {
                "jsonrpc": "2.0",
                "id": msg_id,
                "result": {
                    "content": [
                        {
                            "type": "text",
                            "text": json.dumps(tokens, indent=2)
                        }
                    ]
                }
            }
        except Exception as e:
            return {
                "jsonrpc": "2.0",
                "id": msg_id,
                "result": {
                    "content": [
                        {
                            "type": "text",
                            "text": f"Error loading tokens: {e}"
                        }
                    ],
                    "isError": True
                }
            }
            
    elif name == "update_stitch_tokens":
        try:
            tokens = arguments.get("tokens")
            if not isinstance(tokens, dict):
                raise ValueError("tokens argument must be a JSON object/dictionary.")
                
            STITCH_DESIGN_PATH.parent.mkdir(parents=True, exist_ok=True)
            with open(STITCH_DESIGN_PATH, "w", encoding="utf-8") as f:
                json.dump(tokens, f, indent=2)
                
            log(f"Successfully updated tokens: {list(tokens.keys())}")
            
            return {
                "jsonrpc": "2.0",
                "id": msg_id,
                "result": {
                    "content": [
                        {
                            "type": "text",
                            "text": "Successfully updated stitch_design.json tokens."
                        }
                    ]
                }
            }
        except Exception as e:
            return {
                "jsonrpc": "2.0",
                "id": msg_id,
                "result": {
                    "content": [
                        {
                            "type": "text",
                            "text": f"Error updating tokens: {e}"
                        }
                    ],
                    "isError": True
                }
            }
    else:
        return {
            "jsonrpc": "2.0",
            "id": msg_id,
            "error": {
                "code": -32601,
                "message": f"Method/Tool not found: {name}"
            }
        }

def main():
    log("Server starting up...")
    
    # Read stdin line-by-line
    for line in sys.stdin:
        if not line.strip():
            continue
        try:
            msg = json.loads(line)
            msg_id = msg.get("id")
            method = msg.get("method")
            params = msg.get("params", {})
            
            log(f"Received request: {method} (ID: {msg_id})")
            
            response = None
            if method == "initialize":
                response = handle_initialize(msg_id, params)
            elif method == "notifications/initialized":
                # Notifications do not receive responses
                log("Client initialized connection.")
                continue
            elif method == "tools/list":
                response = handle_list_tools(msg_id)
            elif method == "tools/call":
                response = handle_call_tool(msg_id, params)
            else:
                if msg_id is not None:
                    response = {
                        "jsonrpc": "2.0",
                        "id": msg_id,
                        "error": {
                            "code": -32601,
                            "message": f"Method not found: {method}"
                        }
                    }
                    
            if response is not None:
                sys.stdout.write(json.dumps(response) + "\n")
                sys.stdout.flush()
                
        except Exception as e:
            log(f"Error handling message: {e}")

if __name__ == "__main__":
    main()
