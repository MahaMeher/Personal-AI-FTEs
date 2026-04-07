#!/usr/bin/env python3
"""
Post to Facebook Page using Playwright MCP

Usage: python post_to_facebook.py "Your message here"
"""

import subprocess
import sys
import json

FACEBOOK_PAGE_URL = "https://www.facebook.com/Tech-IT-100691475476827"
MCP_SERVER_URL = "http://localhost:8808"
MCP_CLIENT = r"D:\Personal-AI-FTEs\.qwen\skills\browsing-with-playwright\scripts\mcp-client.py"


def post_to_facebook(message: str) -> dict:
    """Post a message to the Facebook page using Playwright MCP."""
    
    # Escape the message for JavaScript
    escaped_message = message.replace('\\', '\\\\').replace('"', '\\"').replace("'", "\\'")
    
    playwright_code = f"""
async (page) => {{
    const result = {{ success: false, message: '' }};
    
    try {{
        // Navigate to Facebook
        await page.goto('https://www.facebook.com', {{ waitUntil: 'networkidle', timeout: 30000 }});
        await page.waitForTimeout(3000);
        
        // Check if logged in
        const hasLogin = await page.locator('#email').isVisible();
        if (hasLogin) {{
            result.message = 'Not logged in - manual login required';
            return result;
        }}
        
        // Navigate to the Tech-IT page
        await page.goto('{FACEBOOK_PAGE_URL}', {{ waitUntil: 'networkidle', timeout: 30000 }});
        await page.waitForTimeout(2000);
        
        // Find the post composer
        const composer = page.locator('[aria-label="Write a post..."], [placeholder="What\\'s on your mind?"]').first();
        await composer.click();
        await page.waitForTimeout(1000);
        
        // Type the message
        await page.keyboard.type('{escaped_message}');
        await page.waitForTimeout(1000);
        
        // Find and click the Post button
        const postButton = page.locator('button').filter({{ hasText: /Post|Publish/i }}).first();
        await postButton.click();
        await page.waitForTimeout(3000);
        
        result.success = true;
        result.message = 'Post published successfully';
    }} catch (error) {{
        result.message = 'Error: ' + error.message;
    }}
    
    return result;
}}
"""
    
    # Call MCP server
    cmd = [
        sys.executable,
        MCP_CLIENT,
        "call",
        "-u", MCP_SERVER_URL,
        "-t", "browser_run_code",
        "-p", json.dumps({"code": playwright_code})
    ]
    
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)

    print(f"STDOUT: {result.stdout}")
    print(f"STDERR: {result.stderr}")
    print(f"Return code: {result.returncode}")

    if result.returncode != 0:
        return {"success": False, "error": result.stderr or result.stdout}

    try:
        return json.loads(result.stdout)
    except json.JSONDecodeError as e:
        return {"success": False, "error": f"Invalid JSON: {e}, raw: {result.stdout}"}


def main():
    if len(sys.argv) < 2:
        print("Usage: python post_to_facebook.py \"Your message here\"")
        sys.exit(1)
    
    message = " ".join(sys.argv[1:])
    print(f"Posting to Facebook: {message}")
    
    result = post_to_facebook(message)
    
    if result.get("success"):
        print(f"✓ {result.get('message')}")
    else:
        print(f"✗ {result.get('message') or result.get('error')}")
        sys.exit(1)


if __name__ == "__main__":
    main()
