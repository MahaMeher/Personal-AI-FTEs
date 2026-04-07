#!/usr/bin/env python3
"""
Facebook MCP Helper - Start server and execute commands
Gold Tier Feature: Personal AI FTEs Project

Usage:
    python facebook.py post "Your message here"
    python facebook.py info
    python facebook.py posts 5
    python facebook.py comments POST_ID
"""

import sys
import os
import subprocess
import json

# Get the directory where this script is located
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
MCP_CLIENT = os.path.join(SCRIPT_DIR, 'mcp-client.py')
MCP_SERVER = os.path.join(SCRIPT_DIR, 'facebook_mcp_server.py')


def run_mcp_command(tool: str, params: dict):
    """Run an MCP command using the client"""
    # Get the directory where this script is located
    script_dir = os.path.dirname(os.path.abspath(__file__))
    mcp_client = os.path.join(script_dir, 'mcp-client.py')
    mcp_server = os.path.join(script_dir, 'facebook_mcp_server.py')
    
    # Load .env file to get credentials
    env_file = os.path.join(script_dir, '.env')
    
    # If .env doesn't exist in skill folder, try the scripts folder
    if not os.path.exists(env_file):
        env_file = os.path.join(os.path.dirname(script_dir), '..', 'AI_Employee_Vault', 'scripts', '.env')
    
    # Read environment variables from .env
    env = os.environ.copy()
    if os.path.exists(env_file):
        with open(env_file, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    env[key.strip()] = value.strip()
    
    cmd = [
        sys.executable,
        mcp_client,
        'call',
        '--stdio',
        f'python "{mcp_server}"',
        '--tool',
        tool,
        '--params',
        json.dumps(params)
    ]
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30, env=env)
        if result.returncode == 0:
            print(result.stdout)
            return json.loads(result.stdout) if result.stdout.strip() else {}
        else:
            print(f"Error: {result.stderr}")
            return None
    except Exception as e:
        print(f"Error running command: {e}")
        return None


def post_message(message: str, link: str = None):
    """Post a message to Facebook"""
    params = {'message': message, 'published': True}
    if link:
        params['link'] = link
    
    print(f"📱 Posting to Facebook...")
    print(f"📝 Message: {message[:100]}")
    
    result = run_mcp_command('facebook_create_post', params)
    
    if result and 'post_id' in str(result):
        print("✅ Post created successfully!")
        print(f"Result: {result}")
    else:
        print(f"❌ Failed to post: {result}")


def get_page_info():
    """Get Facebook Page information"""
    print("📘 Getting Page Info...\n")
    result = run_mcp_command('facebook_get_page_info', {})
    print(result)


def get_posts(limit: int = 5):
    """Get recent posts"""
    print(f"📱 Getting {limit} recent posts...\n")
    result = run_mcp_command('facebook_get_posts', {'limit': limit})
    print(result)


def get_comments(post_id: str, limit: int = 50):
    """Get comments on a post"""
    print(f"💬 Getting comments on post {post_id}...\n")
    result = run_mcp_command('facebook_get_post_comments', {'post_id': post_id, 'limit': limit})
    print(result)


def show_help():
    """Show usage help"""
    print("""
Facebook MCP Helper - Gold Tier
================================

Usage:
    python facebook.py <command> [arguments]

Commands:
    post "message"              Post a message to Facebook
    post "message" "url"        Post with a link
    info                        Get page information
    posts [count]              Get recent posts (default: 5)
    comments <post_id>         Get comments on a post
    report [days]              Generate engagement report (default: 7)
    help                       Show this help

Examples:
    python facebook.py post "Hello from AI FTE!"
    python facebook.py post "Check this!" "https://example.com"
    python facebook.py info
    python facebook.py posts 10
    python facebook.py comments 123456789_987654321
    python facebook.py report 7
""")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        show_help()
        exit(0)
    
    command = sys.argv[1]
    
    if command == 'help':
        show_help()
    
    elif command == 'post':
        if len(sys.argv) < 3:
            print("❌ Error: Message required")
            show_help()
            exit(1)
        message = sys.argv[2]
        link = sys.argv[3] if len(sys.argv) > 3 else None
        post_message(message, link)
    
    elif command == 'info':
        get_page_info()
    
    elif command == 'posts':
        limit = int(sys.argv[2]) if len(sys.argv) > 2 else 5
        get_posts(limit)
    
    elif command == 'comments':
        if len(sys.argv) < 3:
            print("❌ Error: Post ID required")
            exit(1)
        post_id = sys.argv[2]
        get_comments(post_id)
    
    elif command == 'report':
        days = int(sys.argv[2]) if len(sys.argv) > 2 else 7
        print(f"📊 Generating {days}-day engagement report...\n")
        result = run_mcp_command('facebook_generate_engagement_report', {'days': days})
        print(result)
    
    else:
        print(f"❌ Unknown command: {command}")
        show_help()
        exit(1)
