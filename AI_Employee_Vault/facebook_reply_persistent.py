#!/usr/bin/env python3
"""
Facebook Reply - Persistent MCP Client
Maintains a single HTTP connection to preserve browser state
"""

import json
import sys
from urllib.request import Request, urlopen
from urllib.error import URLError, HTTPError

MCP_URL = "http://localhost:8808/mcp"
POST_URL = "https://www.facebook.com/1101676766351759/posts/122096734502847581"
REPLY_TEXT = "Thank you so much! 🙏"

class PersistentMCPClient:
    """MCP client that maintains a single HTTP session."""
    
    def __init__(self, url):
        self.url = url
        self._request_id = 0
        self._session_id = None
        self._initialized = False
    
    def _next_id(self):
        self._request_id += 1
        return self._request_id
    
    def _ensure_initialized(self):
        if self._initialized:
            return
        
        payload = {
            "jsonrpc": "2.0",
            "id": self._next_id(),
            "method": "initialize",
            "params": {
                "protocolVersion": "2024-11-05",
                "capabilities": {},
                "clientInfo": {"name": "facebook-reply", "version": "1.0.0"}
            }
        }
        
        data = json.dumps(payload).encode('utf-8')
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json, text/event-stream"
        }
        
        req = Request(self.url, data=data, headers=headers, method='POST')
        with urlopen(req, timeout=30) as resp:
            self._session_id = resp.headers.get('Mcp-Session-Id')
            body = resp.read().decode('utf-8')
            # Parse SSE format
            for line in body.split('\n'):
                if line.startswith('data:'):
                    response = json.loads(line[5:].strip())
                    break
        
        self._initialized = True
        
        # Send initialized notification
        self._send_notification("notifications/initialized")
    
    def _send_notification(self, method, params=None):
        payload = {"jsonrpc": "2.0", "method": method}
        if params:
            payload["params"] = params
        
        data = json.dumps(payload).encode('utf-8')
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json, text/event-stream"
        }
        if self._session_id:
            headers["Mcp-Session-Id"] = self._session_id
        
        req = Request(self.url, data=data, headers=headers, method='POST')
        try:
            with urlopen(req, timeout=30) as resp:
                pass
        except:
            pass
    
    def call_tool(self, name, arguments=None):
        """Call a tool and return the result."""
        self._ensure_initialized()
        
        payload = {
            "jsonrpc": "2.0",
            "id": self._next_id(),
            "method": "tools/call",
            "params": {
                "name": name,
                "arguments": arguments or {}
            }
        }
        
        data = json.dumps(payload).encode('utf-8')
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json, text/event-stream"
        }
        if self._session_id:
            headers["Mcp-Session-Id"] = self._session_id
        
        req = Request(self.url, data=data, headers=headers, method='POST')
        
        with urlopen(req, timeout=120) as resp:
            body = resp.read().decode('utf-8')
            # Parse SSE format
            for line in body.split('\n'):
                if line.startswith('data:'):
                    response = json.loads(line[5:].strip())
                    if "result" in response:
                        return response["result"]
                    elif "error" in response:
                        raise Exception(f"MCP Error: {response['error']}")
        
        return None

def main():
    print("=" * 60)
    print("Facebook Comment Reply - Persistent Connection")
    print("=" * 60)
    print(f"Post URL: {POST_URL}")
    print(f"Reply: {REPLY_TEXT}")
    print()
    
    client = PersistentMCPClient(MCP_URL)
    
    try:
        # Step 1: Navigate to Facebook post
        print("Step 1: Navigating to Facebook post...")
        result = client.call_tool("browser_navigate", {"url": POST_URL})
        print(f"  Result: {json.dumps(result, indent=2)[:500]}...")
        
        # Step 2: Wait for page load
        print("\nStep 2: Waiting for page to load...")
        import time
        time.sleep(5)
        
        # Step 3: Take snapshot
        print("\nStep 3: Taking page snapshot...")
        result = client.call_tool("browser_snapshot", {})
        print(f"  Snapshot result: {json.dumps(result, indent=2)[:800]}...")
        
        # Check if logged in
        content_text = str(result)
        if "Log in to Facebook" in content_text or "Email address" in content_text:
            print("\n  *** NOT LOGGED IN ***")
            print("  Please log in to Facebook manually in the browser window.")
            print("  Then run the script again.")
            return
        
        # Step 4: Take screenshot
        print("\nStep 4: Taking screenshot...")
        result = client.call_tool("browser_take_screenshot", {"type": "png"})
        print("  Screenshot saved to .playwright-mcp folder")
        
        # Step 5: Search for and reply to comment
        print("\nStep 5: Searching for comment and replying...")
        
        reply_code = f"""
async (page) => {{
    const result = {{ found: false, replied: false }};
    
    try {{
        // Look for any comment with "good" or "congrats"
        const content = await page.content();
        result.hasKeywords = content.toLowerCase().includes('good') || content.toLowerCase().includes('congrats');
        
        // Find all buttons with "Reply" text
        const replyButtons = page.locator('[role="button"]').filter({{ hasText: /Reply/i }});
        const count = await replyButtons.count();
        result.replyButtonCount = count;
        
        if (count > 0) {{
            result.found = true;
            
            // Click first reply button
            await replyButtons.first().click();
            result.clicked = true;
            await page.waitForTimeout(2000);
            
            // Find reply input and type
            const inputs = page.locator('[role="textbox"], [contenteditable="true"]');
            for (let i = 0; i < await inputs.count(); i++) {{
                const input = inputs.nth(i);
                if (await input.isVisible()) {{
                    await input.fill("{REPLY_TEXT}");
                    result.typed = true;
                    result.inputIndex = i;
                    break;
                }}
            }}
            
            if (result.typed) {{
                await page.keyboard.press('Enter');
                result.replied = true;
                await page.waitForTimeout(2000);
            }}
        }}
        
        result.finalUrl = page.url();
    }} catch (e) {{
        result.error = e.message;
    }}
    
    return result;
}}
"""
        
        result = client.call_tool("browser_run_code", {"code": reply_code})
        print(f"  Reply result: {json.dumps(result, indent=2)}")
        
    except Exception as e:
        print(f"\nError: {e}")
    
    print("\n" + "=" * 60)
    print("Script completed")
    print("=" * 60)

if __name__ == "__main__":
    main()
