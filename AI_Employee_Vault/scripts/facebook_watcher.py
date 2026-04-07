#!/usr/bin/env python3
"""
Facebook Watcher - Monitors Facebook/Instagram for engagement and creates action files

Gold Tier Feature: Personal AI FTEs Project
Monitors Facebook Page and Instagram Business Account for:
- New comments requiring response
- Messages with urgent keywords
- Negative sentiment posts (flag for review)
- High-performing posts (viral alerts)
- Scheduled post reminders
"""

import os
import sys
import json
import time
import logging
import hashlib
from pathlib import Path
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional

import requests
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('facebook_watcher.log')
    ]
)
logger = logging.getLogger('facebook-watcher')

# Configuration
FACEBOOK_ACCESS_TOKEN = os.getenv('FACEBOOK_ACCESS_TOKEN', '')
FACEBOOK_PAGE_ID = os.getenv('FACEBOOK_PAGE_ID', '')
INSTAGRAM_BUSINESS_ACCOUNT_ID = os.getenv('INSTAGRAM_BUSINESS_ACCOUNT_ID', '')
VAULT_PATH = os.getenv('VAULT_PATH', 'D:/Personal-AI-FTEs/AI_Employee_Vault')
CHECK_INTERVAL = int(os.getenv('CHECK_INTERVAL', '120'))  # seconds

# Keywords for urgency detection
URGENT_KEYWORDS = [
    'urgent', 'asap', 'emergency', 'help', 'complaint', 'issue',
    'problem', 'wrong', 'broken', 'refund', 'angry', 'disappointed'
]

# Sentiment indicators (simplified - in production use NLP library)
NEGATIVE_WORDS = [
    'hate', 'terrible', 'awful', 'worst', 'bad', 'poor', 'disappointed',
    'angry', 'frustrated', 'useless', 'waste', 'never', 'unfortunately'
]

POSITIVE_WORDS = [
    'love', 'great', 'awesome', 'best', 'amazing', 'wonderful', 'excellent',
    'fantastic', 'perfect', 'happy', 'satisfied', 'recommend', 'thanks'
]


class FacebookWatcher:
    """Monitor Facebook/Instagram for engagement and create action files"""
    
    def __init__(self, vault_path: str, check_interval: int = 120):
        self.vault_path = Path(vault_path)
        self.needs_action = self.vault_path / 'Needs_Action'
        self.check_interval = check_interval
        self.processed_items = set()
        self.session = requests.Session()
        self.graph_api_base = f'https://graph.facebook.com/v19.0'
        
        # Ensure Needs_Action directory exists
        self.needs_action.mkdir(parents=True, exist_ok=True)
        
        # Load previously processed items
        self._load_processed_items()
        
    def _load_processed_items(self):
        """Load processed item IDs from cache file"""
        cache_file = self.vault_path / '.facebook_processed.json'
        if cache_file.exists():
            try:
                with open(cache_file, 'r') as f:
                    self.processed_items = set(json.load(f))
                logger.info(f"Loaded {len(self.processed_items)} processed items from cache")
            except Exception as e:
                logger.error(f"Error loading cache: {e}")
                self.processed_items = set()
    
    def _save_processed_items(self):
        """Save processed item IDs to cache file"""
        cache_file = self.vault_path / '.facebook_processed.json'
        try:
            # Keep only last 1000 items to prevent file from growing indefinitely
            items_to_save = list(self.processed_items)[-1000:]
            with open(cache_file, 'w') as f:
                json.dump(items_to_save, f)
        except Exception as e:
            logger.error(f"Error saving cache: {e}")
    
    def _get(self, endpoint: str, params: dict = None) -> dict:
        """Make GET request to Graph API"""
        url = f"{self.graph_api_base}/{endpoint}"
        all_params = {'access_token': FACEBOOK_ACCESS_TOKEN}
        if params:
            all_params.update(params)
        
        try:
            response = self.session.get(url, params=all_params, timeout=30)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Graph API GET error: {e}")
            return {}
    
    def _analyze_sentiment(self, text: str) -> str:
        """Simple sentiment analysis (positive/negative/neutral)"""
        text_lower = text.lower()
        
        positive_count = sum(1 for word in POSITIVE_WORDS if word in text_lower)
        negative_count = sum(1 for word in NEGATIVE_WORDS if word in text_lower)
        
        if positive_count > negative_count:
            return 'positive'
        elif negative_count > positive_count:
            return 'negative'
        else:
            return 'neutral'
    
    def _detect_urgency(self, text: str) -> str:
        """Detect if message contains urgent keywords"""
        text_lower = text.lower()
        return any(keyword in text_lower for keyword in URGENT_KEYWORDS)
    
    def _generate_item_id(self, item: dict) -> str:
        """Generate unique ID for an item"""
        content = f"{item.get('id', '')}{item.get('created_time', '')}"
        return hashlib.md5(content.encode()).hexdigest()[:16]
    
    def check_for_updates(self) -> list:
        """Check for new Facebook/Instagram activity"""
        new_items = []
        
        # Check Facebook comments
        try:
            comments = self._get_facebook_comments()
            for comment in comments:
                item_id = self._generate_item_id(comment)
                if item_id not in self.processed_items:
                    comment['item_type'] = 'facebook_comment'
                    new_items.append(comment)
                    self.processed_items.add(item_id)
        except Exception as e:
            logger.error(f"Error checking Facebook comments: {e}")
        
        # Check Facebook messages/conversations
        try:
            conversations = self._get_facebook_conversations()
            for conv in conversations:
                item_id = self._generate_item_id(conv)
                if item_id not in self.processed_items:
                    conv['item_type'] = 'facebook_message'
                    new_items.append(conv)
                    self.processed_items.add(item_id)
        except Exception as e:
            logger.error(f"Error checking Facebook messages: {e}")
        
        # Check Instagram comments
        if INSTAGRAM_BUSINESS_ACCOUNT_ID:
            try:
                ig_comments = self._get_instagram_comments()
                for comment in ig_comments:
                    item_id = self._generate_item_id(comment)
                    if item_id not in self.processed_items:
                        comment['item_type'] = 'instagram_comment'
                        new_items.append(comment)
                        self.processed_items.add(item_id)
            except Exception as e:
                logger.error(f"Error checking Instagram comments: {e}")
        
        # Save cache
        self._save_processed_items()
        
        return new_items
    
    def _get_facebook_comments(self, limit: int = 25) -> list:
        """Get recent comments on Facebook Page posts"""
        # Get recent posts
        posts_result = self._get(f'{FACEBOOK_PAGE_ID}/posts', {'limit': 5})
        posts = posts_result.get('data', [])
        
        all_comments = []
        for post in posts:
            post_id = post['id']
            comments_result = self._get(f'{post_id}/comments', {
                'fields': 'id,from,message,created_time,like_count',
                'limit': limit
            })
            
            comments = comments_result.get('data', [])
            for comment in comments:
                comment['post_id'] = post_id
                comment['post_message'] = post.get('message', '')[:100]
            all_comments.extend(comments)
        
        return all_comments
    
    def _get_facebook_conversations(self, limit: int = 25) -> list:
        """Get recent conversations (messages) from Page"""
        result = self._get(f'{FACEBOOK_PAGE_ID}/conversations', {
            'fields': 'id,from,message,created_time,comment_count,like_count',
            'limit': limit,
            'order': 'chronological'
        })
        return result.get('data', [])
    
    def _get_instagram_comments(self, limit: int = 25) -> list:
        """Get recent comments on Instagram media"""
        # Get recent media
        media_result = self._get(f'{INSTAGRAM_BUSINESS_ACCOUNT_ID}/media', {
            'fields': 'id,caption,media_type,timestamp',
            'limit': 5
        })
        media = media_result.get('data', [])
        
        all_comments = []
        for item in media:
            media_id = item['id']
            comments_result = self._get(f'{media_id}/comments', {
                'fields': 'id,from,text,timestamp',
                'limit': limit
            })
            
            comments = comments_result.get('data', [])
            for comment in comments:
                comment['media_id'] = media_id
                comment['media_caption'] = item.get('caption', '')[:100]
                comment['message'] = comment.get('text', '')  # Normalize field name
            all_comments.extend(comments)
        
        return all_comments
    
    def create_action_file(self, item: dict) -> Optional[Path]:
        """Create .md action file in Needs_Action folder"""
        item_type = item.get('item_type', 'unknown')
        item_id = item.get('id', 'unknown')
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        # Extract common fields
        from_user = item.get('from', {}).get('name', 'Unknown User')
        message = item.get('message', item.get('text', ''))
        created_time = item.get('created_time', item.get('timestamp', datetime.now().isoformat()))
        
        # Analyze sentiment and urgency
        sentiment = self._analyze_sentiment(message)
        is_urgent = self._detect_urgency(message)
        
        # Determine priority
        if is_urgent or sentiment == 'negative':
            priority = 'high'
        elif sentiment == 'positive':
            priority = 'normal'
        else:
            priority = 'low'
        
        # Create filename
        if item_type == 'facebook_comment':
            prefix = 'FACEBOOK_COMMENT'
            post_ref = item.get('post_message', 'unknown')[:20].replace(' ', '_')
        elif item_type == 'facebook_message':
            prefix = 'FACEBOOK_MESSAGE'
            post_ref = 'inbox'
        elif item_type == 'instagram_comment':
            prefix = 'INSTAGRAM_COMMENT'
            post_ref = item.get('media_caption', 'unknown')[:20].replace(' ', '_')
        else:
            prefix = 'SOCIAL_ENGAGEMENT'
            post_ref = 'unknown'
        
        filename = f"{prefix}_{timestamp}_{item_id[:8]}.md"
        filepath = self.needs_action / filename
        
        # Generate suggested response based on sentiment
        suggested_response = self._generate_suggested_response(message, sentiment)
        
        # Create content
        content = f"""---
type: {item_type}
platform: {"Facebook" if "facebook" in item_type else "Instagram"}
item_id: {item_id}
post_id: {item.get('post_id', item.get('media_id', 'N/A'))}
from: {from_user}
message: {message}
sentiment: {sentiment}
urgency: {"high" if is_urgent else "normal"}
priority: {priority}
received: {created_time}
processed: {datetime.now().isoformat()}
status: pending
---

# {"Facebook" if "facebook" in item_type else "Instagram"} {item_type.replace('_', ' ').title()} Requiring Response

## Message Details

**From:** {from_user}
**Platform:** {"Facebook" if "facebook" in item_type else "Instagram"}
**Received:** {created_time}
**Post:** {item.get('post_message', item.get('media_caption', 'N/A'))}

## Message Content

> {message}

## Analysis

- **Sentiment:** {sentiment.upper()}
- **Urgency:** {"🚨 HIGH - Contains urgent keywords" if is_urgent else "✅ Normal"}
- **Priority:** {priority.upper()}

## Suggested Actions

- [ ] {"Respond immediately (urgent/negative)" if is_urgent or sentiment == 'negative' else "Respond within 24 hours"}
- [ ] {"Escalate to human review" if sentiment == 'negative' else "Handle with standard response"}
- [ ] Log interaction in CRM
- [ ] Follow up if needed

## Draft Response

{suggested_response}

## Response Template

```
Hi {from_user.split()[0]},

{suggested_response.split(chr(10))[2] if chr(10) in suggested_response else "Thanks for reaching out!"}

Best regards,
Team
```

---
*Generated by Facebook Watcher - Gold Tier Feature*
"""
        
        try:
            filepath.write_text(content, encoding='utf-8')
            logger.info(f"Created action file: {filepath.name}")
            return filepath
        except Exception as e:
            logger.error(f"Error creating action file: {e}")
            return None
    
    def _generate_suggested_response(self, message: str, sentiment: str) -> str:
        """Generate suggested response based on sentiment"""
        message_lower = message.lower()
        
        if 'price' in message_lower or 'cost' in message_lower:
            return """Thanks for your interest! 

For pricing information, please check our website or send us a direct message with your specific requirements. We'd be happy to provide a customized quote!

Best regards,
Team"""
        
        elif 'when' in message_lower and ('available' in message_lower or 'launch' in message_lower):
            return """Great question! 

We're excited to announce that our product/service will be available soon. Stay tuned to our page for the official launch date!

Best regards,
Team"""
        
        elif sentiment == 'negative':
            return """We're sorry to hear about your experience. 

This is not the level of service we strive to provide. Please send us a direct message with your contact information, and our team will reach out to resolve this issue promptly.

Best regards,
Team"""
        
        elif sentiment == 'positive':
            return """Thank you so much for your kind words! 

We're thrilled to hear that you're happy with our products/services. Your support means the world to us!

Best regards,
Team"""
        
        else:
            return """Thanks for reaching out! 

We appreciate you taking the time to contact us. Our team will review your message and get back to you as soon as possible.

Best regards,
Team"""
    
    def run(self):
        """Main watcher loop"""
        logger.info(f"Starting Facebook Watcher (checking every {self.check_interval}s)")
        logger.info(f"Monitoring Facebook Page: {FACEBOOK_PAGE_ID}")
        if INSTAGRAM_BUSINESS_ACCOUNT_ID:
            logger.info(f"Monitoring Instagram Account: {INSTAGRAM_BUSINESS_ACCOUNT_ID}")
        
        while True:
            try:
                items = self.check_for_updates()
                
                if items:
                    logger.info(f"Found {len(items)} new items")
                    for item in items:
                        filepath = self.create_action_file(item)
                        if filepath:
                            logger.info(f"Created action file: {filepath.name}")
                else:
                    logger.debug("No new activity")
                
            except Exception as e:
                logger.error(f"Error in watcher loop: {e}", exc_info=True)
            
            time.sleep(self.check_interval)


def main():
    """Main entry point"""
    vault_path = VAULT_PATH
    
    # Verify vault exists
    if not Path(vault_path).exists():
        logger.error(f"Vault path does not exist: {vault_path}")
        sys.exit(1)
    
    # Verify Facebook credentials
    if not FACEBOOK_ACCESS_TOKEN or not FACEBOOK_PAGE_ID:
        logger.error("Missing Facebook credentials. Set FACEBOOK_ACCESS_TOKEN and FACEBOOK_PAGE_ID")
        sys.exit(1)
    
    # Create and run watcher
    watcher = FacebookWatcher(vault_path, CHECK_INTERVAL)
    
    try:
        watcher.run()
    except KeyboardInterrupt:
        logger.info("Facebook Watcher stopped by user")
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
