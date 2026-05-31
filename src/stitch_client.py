import os
import json
import sys
import re
from pathlib import Path
import requests
from dotenv import load_dotenv

# Load environment variables
BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")

STITCH_API_KEY = os.environ.get("STITCH_API_KEY")
STITCH_PROJECT_ID = os.environ.get("STITCH_PROJECT_ID")
STITCH_SCREEN_ID = os.environ.get("STITCH_SCREEN_ID")

STITCH_MCP_URL = "https://stitch.googleapis.com/mcp"

# Default theme (Dhan premium dark UI theme)
DEFAULT_THEME = {
    "primary_color": "#E2FF3B",
    "bg_color": "#080A0C",
    "card_bg_color": "#0E1217",
    "border_color": "#1C232E",
    "text_color": "#BAC7D5",
    "text_highlight_color": "#FFFFFF",
    "text_muted_color": "#8A99AD",
    "success_color": "#10B981",
    "danger_color": "#EF4444",
    "font_header": "'Outfit', sans-serif",
    "font_body": "'Plus Jakarta Sans', sans-serif"
}

def write_design_json(design_data):
    target_path = BASE_DIR / "stitch_design.json"
    try:
        with open(target_path, "w") as f:
            json.dump(design_data, f, indent=4)
        print(f"✅ Successfully wrote design tokens to {target_path}")
    except Exception as e:
        print(f"❌ Error writing design file: {e}")

def call_mcp_tool(tool_name, arguments=None):
    if arguments is None:
        arguments = {}
        
    headers = {
        "Content-Type": "application/json",
        "x-goog-api-key": STITCH_API_KEY
    }
    
    payload = {
        "jsonrpc": "2.0",
        "method": "tools/call",
        "params": {
            "name": tool_name,
            "arguments": arguments
        },
        "id": 1
    }
    
    try:
        response = requests.post(STITCH_MCP_URL, headers=headers, json=payload, timeout=15)
        response.raise_for_status()
        resp_json = response.json()
        
        if "error" in resp_json:
            print(f"❌ MCP Server returned error: {resp_json['error']}")
            return None
            
        result = resp_json.get("result", {})
        # MCP tool calls usually return content blocks
        content = result.get("content", [])
        if content and isinstance(content, list):
            text_content = content[0].get("text")
            if text_content:
                try:
                    return json.loads(text_content)
                except json.JSONDecodeError:
                    return text_content
        return result
    except Exception as e:
        print(f"❌ HTTP request to Stitch MCP failed: {e}")
        return None

def extract_tokens_from_payload(payload):
    """
    Scans the JSON response payload for color hex codes and design attributes
    to construct a best-effort stitch_design.json configuration.
    """
    design = DEFAULT_THEME.copy()
    payload_str = json.dumps(payload)
    
    # Try to find all hex colors in the payload
    hex_colors = re.findall(r"#[0-9a-fA-F]{6}\b|#[0-9a-fA-F]{3}\b", payload_str)
    if hex_colors:
        # De-duplicate while preserving order
        unique_colors = []
        for c in hex_colors:
            c_upper = c.upper()
            if c_upper not in unique_colors:
                unique_colors.append(c_upper)
        
        print(f"🎨 Found colors in Stitch design payload: {unique_colors}")
        
        # Best-effort mappings:
        # 1. Dark colors are background candidates
        dark_colors = [c for c in unique_colors if any(x in c for x in ["0", "1", "2"])]
        # 2. Bright colors are primary candidates
        bright_colors = [c for c in unique_colors if c not in dark_colors]
        
        if bright_colors:
            design["primary_color"] = bright_colors[0]
            print(f"👉 Mapped Primary Color to: {design['primary_color']}")
            if len(bright_colors) > 1:
                design["success_color"] = bright_colors[1]
        
        if dark_colors:
            design["bg_color"] = dark_colors[0]
            print(f"👉 Mapped Background Color to: {design['bg_color']}")
            if len(dark_colors) > 1:
                design["card_bg_color"] = dark_colors[1]
                print(f"👉 Mapped Card/Container Background to: {design['card_bg_color']}")
            if len(dark_colors) > 2:
                design["border_color"] = dark_colors[2]

    # Look for font family strings
    fonts = re.findall(r"font-family\s*:\s*['\"]([^'\"]+)['\"]", payload_str)
    if fonts:
        print(f"✍️ Found fonts: {fonts}")
        design["font_body"] = f"'{fonts[0]}', sans-serif"
        if len(fonts) > 1:
            design["font_header"] = f"'{fonts[1]}', sans-serif"
            
    return design

def main():
    print("⚡ Google Stitch Project Integration Client")
    
    if not STITCH_API_KEY:
        print("\n⚠️  No STITCH_API_KEY found in your environment (.env file).")
        print("Creating a template 'stitch_design.json' with default premium styles...")
        write_design_json(DEFAULT_THEME)
        print("\n💡 To sync directly from your stitch.withgoogle.com project:")
        print("1. Log in to stitch.withgoogle.com")
        print("2. Click your profile icon, go to 'Stitch settings' -> 'API keys', and create a key.")
        print("3. Add STITCH_API_KEY=your_key to your .env file.")
        print("4. Re-run this script: python3 src/stitch_client.py")
        return
        
    print("🔑 Authenticated. Querying projects from stitch.googleapis.com...")
    projects_res = call_mcp_tool("list_projects")
    
    if not projects_res:
        print("⚠️ Could not fetch projects. Writing default theme configuration.")
        write_design_json(DEFAULT_THEME)
        return
        
    print(f"Projects Data: {json.dumps(projects_res, indent=2)}")
    
    # Identify project ID
    proj_id = STITCH_PROJECT_ID
    if not proj_id:
        # Fallback to the first project in list if available
        projects_list = projects_res.get("projects", [])
        if projects_list:
            proj_id = projects_list[0].get("id")
            print(f"👉 No STITCH_PROJECT_ID specified. Using first project found: '{projects_list[0].get('name')}' ({proj_id})")
        else:
            print("⚠️ No projects found in your Stitch account.")
            write_design_json(DEFAULT_THEME)
            return

    # List screens in the project
    print(f"🔍 Fetching screens for project '{proj_id}'...")
    screens_res = call_mcp_tool("list_screens", {"projectId": proj_id})
    if not screens_res:
        print("⚠️ Could not list screens. Using default theme.")
        write_design_json(DEFAULT_THEME)
        return

    screens_list = screens_res.get("screens", [])
    screen_id = STITCH_SCREEN_ID
    if not screen_id:
        if screens_list:
            screen_id = screens_list[0].get("id")
            print(f"👉 No STITCH_SCREEN_ID specified. Using first screen: '{screens_list[0].get('name')}' ({screen_id})")
        else:
            print("⚠️ No screens found in project. Using default theme.")
            write_design_json(DEFAULT_THEME)
            return

    # Fetch screen details and extract styling tokens
    print(f"📄 Fetching screen details for screen '{screen_id}'...")
    screen_details = call_mcp_tool("get_screen", {"projectId": proj_id, "screenId": screen_id})
    
    if screen_details:
        print("✨ Screen details retrieved successfully! Extracting design tokens...")
        stitch_theme = extract_tokens_from_payload(screen_details)
        write_design_json(stitch_theme)
    else:
        print("⚠️ Could not fetch screen details. Writing default theme.")
        write_design_json(DEFAULT_THEME)

if __name__ == "__main__":
    main()
