#!/usr/bin/env python3
"""
Reply to Facebook Comment - Simple Script
Usage: python reply_to_comment.py COMMENT_ID "Your reply message"
"""
import os
import sys
import requests
from dotenv import load_dotenv

load_dotenv()

FACEBOOK_ACCESS_TOKEN = os.getenv('FACEBOOK_ACCESS_TOKEN')

if len(sys.argv) < 3:
    print("Usage: python reply_to_comment.py COMMENT_ID \"Your message\"")
    print("Example: python reply_to_comment.py 123456 \"Thanks!\"")
    sys.exit(1)

comment_id = sys.argv[1]
message = sys.argv[2]

url = f"https://graph.facebook.com/v19.0/{comment_id}/comments"
params = {
    'access_token': FACEBOOK_ACCESS_TOKEN,
    'message': message
}

try:
    response = requests.post(url, params=params, timeout=30)
    result = response.json()
    
    if 'id' in result:
        print(f"✅ Reply posted successfully!")
        print(f"Comment ID: {result['id']}")
        print(f"Message: {message}")
    else:
        print(f"❌ Error: {result}")
        sys.exit(1)
except Exception as e:
    print(f"❌ Error: {e}")
    sys.exit(1)
