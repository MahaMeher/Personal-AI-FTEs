#!/usr/bin/env python3
"""Facebook Reply Script - Reply to Maha Zehra's comment"""

import subprocess
import json
import sys

MCP_URL = "http://localhost:8808"
POST_URL = "https://www.facebook.com/1101676766351759/posts/122096734502847581"
REPLY_TEXT = "Thank you so much! 🙏"

def run_mcp_tool(tool_name, params):
    """Run an MCP tool via the client script."""
    cmd = [
        sys.executable,
        r"D:\Personal-AI-FTEs\.qwen\skills\browsing-with-playwright\scripts\mcp-client.py",
        "call",
        "--url", MCP_URL,
        "--tool", tool_name,
        "--params", json.dumps(params)
    ]
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
    if result.returncode != 0:
        print(f"Error running {tool_name}: {result.stderr}")
        return None
    try:
        return json.loads(result.stdout)
    except json.JSONDecodeError:
        print(f"Invalid JSON response: {result.stdout}")
        return None

def main():
    print("=" * 60)
    print("Facebook Comment Reply Script")
    print("=" * 60)
    print(f"Post URL: {POST_URL}")
    print(f"Reply: {REPLY_TEXT}")
    print()

    # Step 1: Navigate to Facebook post
    print("Step 1: Navigating to Facebook post...")
    result = run_mcp_tool("browser_navigate", {"url": POST_URL})
    if result:
        print(f"  Navigation result: {json.dumps(result, indent=2)[:500]}")
    else:
        print("  Failed to navigate")
        return

    # Wait for page load
    print("\nStep 2: Waiting for page to load...")
    result = run_mcp_tool("browser_wait_for", {"time": 5000})
    if result:
        print("  Page loaded")

    # Step 3: Take snapshot to see page structure
    print("\nStep 3: Taking page snapshot...")
    result = run_mcp_tool("browser_snapshot", {})
    if result:
        content = result.get("content", [])
        for item in content:
            if item.get("type") == "text":
                text = item.get("text", "")
                print(f"  Snapshot: {text[:1000]}...")
                # Check if we're logged in
                if "Log in" in text and "Email address" in text:
                    print("\n  *** NOT LOGGED IN - Need to authenticate first ***")
                    print("  Please log in to Facebook manually in the browser window.")
                    return
                elif "What's on your mind" in text or "feed" in text.lower():
                    print("\n  ✓ Logged in successfully")

    # Step 4: Take screenshot for visual confirmation
    print("\nStep 4: Taking screenshot...")
    result = run_mcp_tool("browser_take_screenshot", {"type": "png"})
    if result:
        print("  Screenshot taken - check .playwright-mcp folder")

    # Step 5: Try to find and click reply on the comment
    print("\nStep 5: Looking for comment reply button...")
    
    # Try to search for the comment by text content
    reply_code = """
async (page) => {
    const result = { found: false, replied: false };
    
    // Try to find the comment by Maha Zehra
    try {
        // Look for comment containing "good" or "congrats"
        const commentLocator = page.locator('[data-visualcompletion="css-img"], [role="article"]').filter({ hasText: /good.*congrats|congrats.*good/i });
        const count = await commentLocator.count();
        result.commentsFound = count;
        
        if (count > 0) {
            result.found = true;
            
            // Try to find reply button within the comment
            const replyButton = commentLocator.locator('[role="button"]').filter({ hasText: /Reply/i }).first();
            const replyVisible = await replyButton.isVisible();
            
            if (replyVisible) {
                await replyButton.click();
                result.replyClicked = true;
                
                // Wait for reply input to appear
                await page.waitForTimeout(1000);
                
                // Find the reply input and type our message
                const replyInput = page.locator('[role="textbox"], [contenteditable="true"], input[type="text"]').filter({ hasText: /Write a reply|Reply/i }).first();
                
                // If the above doesn't work, try a more general approach
                if (!await replyInput.isVisible()) {
                    const allInputs = page.locator('[role="textbox"], [contenteditable="true"]');
                    for (let i = 0; i < await allInputs.count(); i++) {
                        const input = allInputs.nth(i);
                        if (await input.isVisible()) {
                            result.selectedInput = i;
                            await input.fill("Thank you so much! 🙏");
                            result.replied = true;
                            break;
                        }
                    }
                } else {
                    await replyInput.fill("Thank you so much! 🙏");
                    result.replied = true;
                }
                
                // Press Enter to submit
                await page.keyboard.press('Enter');
                result.submitted = true;
            } else {
                result.replyButtonVisible = false;
            }
        }
    } catch (e) {
        result.error = e.message;
    }
    
    return result;
}
"""
    
    result = run_mcp_tool("browser_run_code", {"code": reply_code})
    if result:
        print(f"  Reply attempt result: {json.dumps(result, indent=2)}")
    
    print("\n" + "=" * 60)
    print("Script completed")
    print("=" * 60)

if __name__ == "__main__":
    main()
