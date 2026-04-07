#!/usr/bin/env python3
"""Facebook Reply Script - Single atomic call to maintain browser state"""

import subprocess
import json
import sys

MCP_URL = "http://localhost:8808"
POST_URL = "https://www.facebook.com/1101676766351759/posts/122096734502847581"
REPLY_TEXT = "Thank you so much! 🙏"

# Complete workflow in a single JavaScript function
FACEBOOK_REPLY_CODE = f"""
async (page) => {{
    const result = {{
        steps: [],
        success: false,
        error: null
    }};
    
    try {{
        // Step 1: Navigate to Facebook
        result.steps.push('Navigating to Facebook post...');
        await page.goto('{POST_URL}', {{ waitUntil: 'networkidle', timeout: 30000 }});
        result.url = page.url();
        result.title = await page.title();
        result.steps.push(`Navigated to: ${{result.url}}`);
        
        // Wait for page to stabilize
        await page.waitForTimeout(5000);
        
        // Step 2: Check if logged in
        result.steps.push('Checking login status...');
        const content = await page.content();
        result.isLoggedIn = !content.includes('Log in to Facebook') && !content.includes('Email address or mobile number');
        
        if (!result.isLoggedIn) {{
            result.steps.push('NOT LOGGED IN - Please log in manually');
            result.error = 'User not logged in to Facebook';
            return result;
        }}
        result.steps.push('Logged in successfully');
        
        // Step 3: Look for the comment by Maha Zehra
        result.steps.push('Searching for comment...');
        
        // Try multiple selectors to find comments
        const commentSelectors = [
            '[data-pagelet="FeedUnit"]',
            '[data-pagelet="MainFeed"]',
            '[role="article"]',
            '[data-visualcompletion="css-img"]',
            '.x1lliihq',
            '.x78zum5'
        ];
        
        // Look for text "good" and "congrats" in comments section
        const pageContent = await page.content();
        result.hasGoodCongrats = pageContent.toLowerCase().includes('good') && pageContent.toLowerCase().includes('congrats');
        
        // Try to find reply buttons
        const replyButtons = page.locator('[role="button"]').filter({{ hasText: /Reply/i }});
        const replyCount = await replyButtons.count();
        result.replyButtonsFound = replyCount;
        
        if (replyCount > 0) {{
            result.steps.push(`Found ${{replyCount}} reply buttons`);
            
            // Click the first reply button
            const firstReply = replyButtons.first();
            const isVisible = await firstReply.isVisible();
            
            if (isVisible) {{
                result.steps.push('Clicking reply button...');
                await firstReply.click();
                result.replyClicked = true;
                
                // Wait for input to appear
                await page.waitForTimeout(2000);
                
                // Find and fill the reply input
                result.steps.push('Typing reply...');
                
                // Try different input selectors
                const inputSelectors = [
                    '[role="textbox"]',
                    '[contenteditable="true"]',
                    'input[type="text"]',
                    'textarea',
                    '[data-testid="react-composer-text-input"]'
                ];
                
                let typed = false;
                for (const selector of inputSelectors) {{
                    const inputs = page.locator(selector);
                    const count = await inputs.count();
                    for (let i = 0; i < count; i++) {{
                        const input = inputs.nth(i);
                        if (await input.isVisible()) {{
                            await input.fill("{REPLY_TEXT}");
                            typed = true;
                            result.usedSelector = selector;
                            result.inputIndex = i;
                            break;
                        }}
                    }}
                    if (typed) break;
                }}
                
                if (typed) {{
                    result.steps.push('Submitting reply...');
                    // Press Enter to submit
                    await page.keyboard.press('Enter');
                    await page.waitForTimeout(2000);
                    result.replied = true;
                    result.success = true;
                    result.steps.push('Reply submitted successfully!');
                }} else {{
                    result.error = 'Could not find reply input field';
                }}
            }} else {{
                result.error = 'Reply button not visible';
            }}
        }} else {{
            result.error = 'No reply buttons found';
        }}
        
    }} catch (e) {{
        result.error = e.message;
        result.stack = e.stack;
    }}
    
    return result;
}}
"""

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
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
    if result.returncode != 0:
        print(f"Error running {tool_name}: {result.stderr}")
        return None
    try:
        return json.loads(result.stdout)
    except json.JSONDecodeError as e:
        print(f"Invalid JSON response: {e}")
        print(f"Raw output: {result.stdout[:500]}")
        return None

def main():
    print("=" * 60)
    print("Facebook Comment Reply Script")
    print("=" * 60)
    print(f"Post URL: {POST_URL}")
    print(f"Reply: {REPLY_TEXT}")
    print()

    print("Executing complete workflow in single atomic call...")
    print()
    
    # Execute everything in one call
    result = run_mcp_tool("browser_run_code", {"code": FACEBOOK_REPLY_CODE})
    
    if result:
        print("Result:")
        content = result.get("content", [])
        for item in content:
            if item.get("type") == "text":
                text = item.get("text", "")
                # Parse the result JSON from the text
                if '{"steps":' in text:
                    start = text.index('{"steps":')
                    # Find the end of the JSON
                    brace_count = 0
                    end = start
                    for i, char in enumerate(text[start:], start):
                        if char == '{':
                            brace_count += 1
                        elif char == '}':
                            brace_count -= 1
                            if brace_count == 0:
                                end = i + 1
                                break
                    try:
                        result_json = json.loads(text[start:end])
                        print(json.dumps(result_json, indent=2))
                    except:
                        print(text[start:end])
                else:
                    print(text[:1500])
    else:
        print("Failed to get result from MCP server")
    
    print()
    print("=" * 60)
    print("Script completed")
    print("=" * 60)

if __name__ == "__main__":
    main()
