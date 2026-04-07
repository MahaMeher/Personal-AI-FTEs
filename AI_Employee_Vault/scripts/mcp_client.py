"""
MCP Client

Command-line client for testing Universal MCP Server.
"""

import argparse
import json
import sys
from pathlib import Path


def call_tool(tool: str, params: dict, server_url: str = None):
    """
    Call MCP tool.
    
    Args:
        tool: Tool name (send_message, browser_action, etc.)
        params: Tool parameters
        server_url: MCP server URL (if remote)
    """
    # For local testing, import server directly
    sys.path.insert(0, str(Path(__file__).parent))
    
    from mcp_server import UniversalMCPServer
    
    server = UniversalMCPServer()
    
    try:
        if tool == 'send_message':
            channel = params.pop('channel', 'email')
            result = server.send_message(channel=channel, **params)
        elif tool == 'browser_action':
            action = params.pop('action', 'navigate')
            result = server.browser_action(action=action, **params)
        elif tool == 'get_status':
            result = server.get_status()
        elif tool == 'list_contacts':
            channel = params.pop('channel', 'email')
            result = server.list_contacts(channel=channel, **params)
        else:
            result = {
                'success': False,
                'error': f'Unknown tool: {tool}'
            }
            
        print(json.dumps(result, indent=2))
        
    finally:
        server.close()


def main():
    parser = argparse.ArgumentParser(description='MCP Client')
    parser.add_argument('command', choices=['call', 'status', 'interactive'],
                       help='Command to run')
    parser.add_argument('-t', '--tool', help='Tool name')
    parser.add_argument('-p', '--params', help='JSON parameters')
    parser.add_argument('-u', '--url', help='Server URL (for remote)')
    
    args = parser.parse_args()
    
    if args.command == 'status':
        call_tool('get_status', {})
        
    elif args.command == 'call':
        if not args.tool:
            print("Error: --tool required for call command")
            sys.exit(1)
            
        params = json.loads(args.params) if args.params else {}
        call_tool(args.tool, params, args.url)
        
    elif args.command == 'interactive':
        print("MCP Client Interactive Mode")
        print("Commands:")
        print("  status - Get adapter status")
        print("  send <channel> <to> <message> - Send message")
        print("  browser <action> [params] - Browser action")
        print("  quit - Exit")
        
        while True:
            try:
                cmd = input("\nmcp> ").strip()
                
                if cmd.lower() == 'quit':
                    break
                elif cmd.lower() == 'status':
                    call_tool('get_status', {})
                elif cmd.lower().startswith('send '):
                    parts = cmd.split(' ', 3)
                    if len(parts) >= 4:
                        channel = parts[1]
                        to = parts[2]
                        message = parts[3]
                        call_tool('send_message', {
                            'channel': channel,
                            'to': to,
                            'message': message
                        })
                    else:
                        print("Usage: send <channel> <to> <message>")
                elif cmd.lower().startswith('browser '):
                    parts = cmd.split(' ', 2)
                    action = parts[1]
                    params = json.loads(parts[2]) if len(parts) > 2 else {}
                    call_tool('browser_action', {'action': action, **params})
                else:
                    print("Unknown command")
                    
            except KeyboardInterrupt:
                break
            except Exception as e:
                print(f"Error: {e}")


if __name__ == '__main__':
    main()
