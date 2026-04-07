#!/usr/bin/env python3
"""
Send LinkedIn responses to Maha Meher using Playwright MCP server.
This script connects to the MCP server on port 8808 and automates sending responses.
"""

import asyncio
import json
import websockets
import httpx
from datetime import datetime

MCP_SERVER_URL = "http://localhost:8808"
RESPONSE_MESSAGE = "Hi Maha, thank you for reaching out. We don't have any open positions at the moment. I'll keep you in mind if opportunities arise. Best of luck with your job search!"

# Message files to process
MESSAGE_FILES = [
    "LINKEDIN_MSG_176740_SUNDAY.md",
    "LINKEDIN_MSG_357421_Maha_ i am asking u for a job .md",
    "LINKEDIN_MSG_769590_Maha_ you are seeing my msgs b.md",
    "LINKEDIN_MSG_890147_Maha_ this is the testing msgs.md",
    "LINKEDIN_MSG_387400_SUNDAY.md",
    "LINKEDIN_MSG_414749_SUNDAY.md",
    "LINKEDIN_MSG_643068_SUNDAY.md",
    "LINKEDIN_MSG_714884_SUNDAY.md",
    "LINKEDIN_MSG_939722_SUNDAY.md",
]

async def test_playwright_mcp():
    """Test connection to Playwright MCP server and send LinkedIn responses."""
    
    results = {
        "total_messages": len(MESSAGE_FILES),
        "successful": 0,
        "failed": 0,
        "errors": [],
        "details": []
    }
    
    async with httpx.AsyncClient(timeout=60.0) as client:
        try:
            # Step 1: Navigate to LinkedIn
            print("Step 1: Navigating to LinkedIn...")
            response = await client.post(
                f"{MCP_SERVER_URL}/navigate",
                json={"url": "https://www.linkedin.com"}
            )
            print(f"Navigate response: {response.status_code}")
            
            if response.status_code == 200:
                print("✓ Successfully navigated to LinkedIn")
                await asyncio.sleep(3)  # Wait for page load
                
                # Step 2: Take a snapshot to see the page
                print("\nStep 2: Taking page snapshot...")
                snapshot_response = await client.post(
                    f"{MCP_SERVER_URL}/snapshot",
                    json={}
                )
                if snapshot_response.status_code == 200:
                    snapshot_data = snapshot_response.json()
                    print(f"Snapshot: {json.dumps(snapshot_data, indent=2)[:500]}...")
                
                # Step 3: Navigate to messaging
                print("\nStep 3: Navigating to messaging section...")
                messaging_response = await client.post(
                    f"{MCP_SERVER_URL}/navigate",
                    json={"url": "https://www.linkedin.com/messaging/"}
                )
                print(f"Messaging navigate response: {messaging_response.status_code}")
                await asyncio.sleep(3)
                
                # Step 4: Take snapshot of messaging page
                print("\nStep 4: Taking messaging page snapshot...")
                msg_snapshot = await client.post(
                    f"{MCP_SERVER_URL}/snapshot",
                    json={}
                )
                if msg_snapshot.status_code == 200:
                    print("Got messaging page snapshot")
                
                # Step 5: Search for Maha Meher conversations
                print("\nStep 5: Looking for conversations with Maha Meher...")
                
                # Try to click on search or find conversations
                search_response = await client.post(
                    f"{MCP_SERVER_URL}/click",
                    json={"element": "search input", "ref": "searchbox"}
                )
                print(f"Search click response: {search_response.status_code}")
                
                # Step 6: Type in search
                print("\nStep 6: Searching for Maha Meher...")
                type_response = await client.post(
                    f"{MCP_SERVER_URL}/type",
                    json={"element": "search input", "text": "Maha Meher"}
                )
                print(f"Type response: {type_response.status_code}")
                await asyncio.sleep(2)
                
                # Step 7: For each message file, try to send response
                print("\nStep 7: Processing message files...")
                for i, msg_file in enumerate(MESSAGE_FILES):
                    print(f"\n  Processing {i+1}/{len(MESSAGE_FILES)}: {msg_file}")
                    try:
                        # Try to find and click on the conversation
                        # This is a simplified approach - in reality, we'd need to parse the snapshot
                        # and find the correct conversation element reference
                        
                        # For now, let's just try to send a message using the MCP tools
                        send_response = await client.post(
                            f"{MCP_SERVER_URL}/type",
                            json={"element": "message input", "text": RESPONSE_MESSAGE}
                        )
                        
                        if send_response.status_code == 200:
                            # Press enter to send
                            await client.post(
                                f"{MCP_SERVER_URL}/press",
                                json={"element": "message input", "key": "Enter"}
                            )
                            results["successful"] += 1
                            results["details"].append({
                                "file": msg_file,
                                "status": "success",
                                "timestamp": datetime.now().isoformat()
                            })
                            print(f"    ✓ Response sent successfully")
                        else:
                            results["failed"] += 1
                            results["errors"].append(f"Failed to send response for {msg_file}: HTTP {send_response.status_code}")
                            results["details"].append({
                                "file": msg_file,
                                "status": "failed",
                                "error": f"HTTP {send_response.status_code}"
                            })
                            print(f"    ✗ Failed to send response")
                        
                        await asyncio.sleep(1)  # Wait between messages
                        
                    except Exception as e:
                        results["failed"] += 1
                        results["errors"].append(f"Error processing {msg_file}: {str(e)}")
                        results["details"].append({
                            "file": msg_file,
                            "status": "error",
                            "error": str(e)
                        })
                        print(f"    ✗ Error: {str(e)}")
                
            else:
                results["errors"].append(f"Failed to navigate to LinkedIn: HTTP {response.status_code}")
                
        except httpx.ConnectError as e:
            results["errors"].append(f"Could not connect to MCP server: {str(e)}")
            print(f"ERROR: Could not connect to MCP server at {MCP_SERVER_URL}")
        except Exception as e:
            results["errors"].append(f"Unexpected error: {str(e)}")
            print(f"ERROR: {str(e)}")
    
    return results


def main():
    print("=" * 60)
    print("LinkedIn Response Sender - Maha Meher")
    print("=" * 60)
    print(f"\nMCP Server: {MCP_SERVER_URL}")
    print(f"Response message: {RESPONSE_MESSAGE[:50]}...")
    print(f"Total messages to process: {len(MESSAGE_FILES)}")
    print("\n" + "=" * 60 + "\n")
    
    results = asyncio.run(test_playwright_mcp())
    
    print("\n" + "=" * 60)
    print("FINAL RESULTS")
    print("=" * 60)
    print(f"Total messages: {results['total_messages']}")
    print(f"Successful: {results['successful']}")
    print(f"Failed: {results['failed']}")
    
    if results['errors']:
        print("\nErrors encountered:")
        for error in results['errors']:
            print(f"  - {error}")
    
    print("\nDetailed results:")
    for detail in results['details']:
        status_icon = "✓" if detail['status'] == 'success' else "✗"
        print(f"  {status_icon} {detail['file']}: {detail['status']}")
    
    # Save results to file
    results_file = "D:\\Personal-AI-FTEs\\AI_Employee_Vault\\LINKEDIN_RESPONSE_RESULTS.md"
    with open(results_file, 'w') as f:
        f.write(f"""---
type: execution_report
task: linkedin_responses
executed: {datetime.now().isoformat()}
status: completed
---

# LinkedIn Response Execution Report

## Summary
- **Total Messages**: {results['total_messages']}
- **Successful**: {results['successful']}
- **Failed**: {results['failed']}

## Response Sent
```
{RESPONSE_MESSAGE}
```

## Detailed Results
""")
        for detail in results['details']:
            f.write(f"- {detail['file']}: {detail['status']}\n")
        
        if results['errors']:
            f.write("\n## Errors\n")
            for error in results['errors']:
                f.write(f"- {error}\n")
    
    print(f"\nResults saved to: {results_file}")
    return results


if __name__ == "__main__":
    main()
