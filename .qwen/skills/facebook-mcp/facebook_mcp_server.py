#!/usr/bin/env python3
"""
Facebook/Instagram MCP Server - Model Context Protocol Server for Meta Platforms Integration

This MCP server provides tools for interacting with Facebook Pages and Instagram Business
accounts via the Meta Graph API for social media automation and analytics.

Gold Tier Feature: Personal AI FTEs Project
"""

import asyncio
import json
import logging
import os
from typing import Any, Optional
from datetime import datetime, timedelta
from pathlib import Path

import requests
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('facebook-mcp')

# Environment variables
FACEBOOK_APP_ID = os.getenv('FACEBOOK_APP_ID', '')
FACEBOOK_APP_SECRET = os.getenv('FACEBOOK_APP_SECRET', '')
FACEBOOK_ACCESS_TOKEN = os.getenv('FACEBOOK_ACCESS_TOKEN', '')
FACEBOOK_PAGE_ID = os.getenv('FACEBOOK_PAGE_ID', '')
INSTAGRAM_BUSINESS_ACCOUNT_ID = os.getenv('INSTAGRAM_BUSINESS_ACCOUNT_ID', '')

# Meta Graph API endpoints
GRAPH_API_VERSION = 'v19.0'
GRAPH_API_BASE = f'https://graph.facebook.com/{GRAPH_API_VERSION}'


class FacebookClient:
    """Client for Meta Graph API"""
    
    def __init__(self, access_token: str, page_id: str, instagram_account_id: str = None):
        self.access_token = access_token
        self.page_id = page_id
        self.instagram_account_id = instagram_account_id
        self.session = requests.Session()
        self.session.params = {'access_token': access_token}
        
    def _get(self, endpoint: str, params: dict = None) -> dict:
        """Make GET request to Graph API"""
        url = f"{GRAPH_API_BASE}/{endpoint}"
        all_params = self.session.params.copy()
        if params:
            all_params.update(params)
        
        try:
            response = self.session.get(url, params=all_params, timeout=30)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Graph API GET error: {e}")
            raise Exception(f"Facebook API error: {str(e)}")
    
    def _post(self, endpoint: str, data: dict = None) -> dict:
        """Make POST request to Graph API"""
        url = f"{GRAPH_API_BASE}/{endpoint}"
        all_params = self.session.params.copy()
        
        try:
            response = self.session.post(url, params=all_params, json=data, timeout=30)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Graph API POST error: {e}")
            raise Exception(f"Facebook API error: {str(e)}")
    
    def _delete(self, endpoint: str) -> dict:
        """Make DELETE request to Graph API"""
        url = f"{GRAPH_API_BASE}/{endpoint}"
        all_params = self.session.params.copy()
        
        try:
            response = self.session.delete(url, params=all_params, timeout=30)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Graph API DELETE error: {e}")
            raise Exception(f"Facebook API error: {str(e)}")
    
    # Page Methods
    def get_page_info(self) -> dict:
        """Get Facebook Page information"""
        fields = 'id,name,username,about,category,followers_count,likes,talking_about_count,website,emails,phone'
        return self._get(self.page_id, {'fields': fields})
    
    def get_page_posts(self, limit: int = 25, since: str = None, until: str = None) -> list:
        """Get posts from Facebook Page"""
        params = {
            'fields': 'id,message,created_time,updated_time,permalink_url,shares,likes.summary(true),comments.summary(true)',
            'limit': limit
        }
        if since:
            params['since'] = since
        if until:
            params['until'] = until
        
        result = self._get(f'{self.page_id}/posts', params)
        return result.get('data', [])
    
    def create_page_post(self, message: str, link: str = None, photo_url: str = None,
                        published: bool = True) -> dict:
        """Create a new post on Facebook Page"""
        data = {
            'message': message,
            'published': published
        }
        
        if link:
            data['link'] = link
        if photo_url:
            data['attached_media'] = json.dumps([{'media_url': photo_url}])
        
        result = self._post(f'{self.page_id}/feed', data)
        return result
    
    def delete_page_post(self, post_id: str) -> bool:
        """Delete a Facebook Page post"""
        result = self._delete(post_id)
        return result.get('success', False)
    
    # Instagram Methods
    def get_instagram_account_info(self) -> dict:
        """Get Instagram Business Account information"""
        if not self.instagram_account_id:
            raise Exception("Instagram Business Account ID not configured")
        
        fields = 'id,username,biography,website,followers_count,follows_count,media_count'
        return self._get(self.instagram_account_id, {'fields': fields})
    
    def get_instagram_media(self, limit: int = 25) -> list:
        """Get media from Instagram Business Account"""
        if not self.instagram_account_id:
            raise Exception("Instagram Business Account ID not configured")
        
        params = {
            'fields': 'id,caption,media_type,media_url,permalink,timestamp,like_count,comments_count',
            'limit': limit
        }
        
        result = self._get(f'{self.instagram_account_id}/media', params)
        return result.get('data', [])
    
    def create_instagram_media_container(self, caption: str, media_type: str = 'TEXT',
                                         image_url: str = None, video_url: str = None,
                                         is_carousel: bool = False) -> dict:
        """Create Instagram media container (first step to publish)"""
        if not self.instagram_account_id:
            raise Exception("Instagram Business Account ID not configured")
        
        data = {
            'caption': caption,
            'media_type': media_type
        }
        
        if image_url:
            data['image_url'] = image_url
        if video_url:
            data['video_url'] = video_url
        if is_carousel:
            data['is_carousel_item'] = True
        
        result = self._post(f'{self.instagram_account_id}/media', data)
        return result
    
    def publish_instagram_media(self, container_id: str) -> dict:
        """Publish Instagram media container (second step)"""
        if not self.instagram_account_id:
            raise Exception("Instagram Business Account ID not configured")
        
        data = {
            'creation_id': container_id,
            'media_type': 'TEXT'  # Will be overridden by container
        }
        
        result = self._post(f'{self.instagram_account_id}/media_publish', data)
        return result
    
    def get_instagram_insights(self, metric: str = None, period: str = 'day') -> dict:
        """Get Instagram Business Account insights/analytics"""
        if not self.instagram_account_id:
            raise Exception("Instagram Business Account ID not configured")
        
        metrics = metric or 'impressions,reach,profile_views,follower_count,email_button_taps,website_clicks'
        
        params = {
            'metric': metrics,
            'period': period
        }
        
        result = self._get(f'{self.instagram_account_id}/insights', params)
        return result.get('data', [])
    
    # Comments and Engagement
    def get_page_conversations(self, limit: int = 25) -> list:
        """Get conversations (comments and messages) from Page"""
        params = {
            'fields': 'id,from,message,created_time,comment_count,like_count',
            'limit': limit,
            'order': 'chronological'
        }
        
        result = self._get(f'{self.page_id}/conversations', params)
        return result.get('data', [])
    
    def get_post_comments(self, post_id: str, limit: int = 50) -> list:
        """Get comments on a specific post"""
        params = {
            'fields': 'id,from,message,created_time,like_count',
            'limit': limit
        }
        
        result = self._get(f'{post_id}/comments', params)
        return result.get('data', [])
    
    def create_comment(self, object_id: str, message: str) -> dict:
        """Create a comment on a post or object"""
        data = {
            'message': message
        }
        
        result = self._post(f'{object_id}/comments', data)
        return result
    
    def like_object(self, object_id: str) -> bool:
        """Like a post or comment"""
        result = self._post(f'{object_id}/likes', {})
        return result.get('success', False)
    
    # Insights and Analytics
    def get_page_insights(self, metrics: list = None, since: str = None, until: str = None) -> list:
        """Get Facebook Page insights/analytics"""
        default_metrics = [
            'page_impressions_unique',
            'page_reach',
            'page_engaged_users',
            'page_post_engagements_unique',
            'page_likes',
            'page_follows',
            'page_video_views_unique'
        ]
        
        metrics_list = metrics or default_metrics
        
        params = {
            'metric': ','.join(metrics_list)
        }
        
        if since:
            params['since'] = since
        if until:
            params['until'] = until
        
        result = self._get(f'{self.page_id}/insights', params)
        return result.get('data', [])
    
    def get_post_insights(self, post_id: str) -> dict:
        """Get insights for a specific post"""
        metrics = 'post_impressions_unique,post_engagements,post_clicks,post_shares,post_comments,post_reactions_by_type_total'
        
        params = {'fields': metrics}
        result = self._get(post_id, params)
        return result
    
    def generate_engagement_report(self, days: int = 7) -> dict:
        """Generate engagement report for the last N days"""
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        since = start_date.strftime('%Y-%m-%d')
        until = end_date.strftime('%Y-%m-%d')
        
        # Get page insights
        insights = self.get_page_insights(since=since, until=until)
        
        # Get posts
        posts = self.get_page_posts(limit=50)
        
        # Calculate totals
        report = {
            'period': f'{since} to {until}',
            'days': days,
            'metrics': {},
            'posts_count': len(posts),
            'top_posts': []
        }
        
        # Process insights
        for insight in insights:
            name = insight.get('name', 'unknown')
            values = insight.get('values', [])
            total = sum(v.get('value', 0) for v in values if v.get('value'))
            report['metrics'][name] = total
        
        # Get top posts by engagement
        for post in posts[:5]:
            post_insights = self.get_post_insights(post['id'])
            report['top_posts'].append({
                'id': post['id'],
                'message': post.get('message', '')[:100],
                'created_time': post.get('created_time'),
                'permalink': post.get('permalink_url'),
                'insights': post_insights
            })
        
        return report
    
    # Scheduled Posts
    def get_scheduled_posts(self) -> list:
        """Get scheduled posts from Page"""
        params = {
            'fields': 'id,message,scheduled_publish_time,created_time',
            'published': 'false'
        }
        
        result = self._get(f'{self.page_id}/scheduled_posts', params)
        return result.get('data', [])
    
    def schedule_page_post(self, message: str, scheduled_time: str, 
                          link: str = None, photo_url: str = None) -> dict:
        """Schedule a post for future publishing"""
        data = {
            'message': message,
            'published': False,
            'scheduled_publish_time': int(datetime.strptime(scheduled_time, '%Y-%m-%d %H:%M:%S').timestamp())
        }
        
        if link:
            data['link'] = link
        if photo_url:
            data['attached_media'] = json.dumps([{'media_url': photo_url}])
        
        result = self._post(f'{self.page_id}/scheduled_posts', data)
        return result


# Initialize Facebook client
facebook_client = FacebookClient(
    FACEBOOK_ACCESS_TOKEN,
    FACEBOOK_PAGE_ID,
    INSTAGRAM_BUSINESS_ACCOUNT_ID
)

# Create MCP server
app = Server("facebook-mcp")


@app.list_tools()
async def list_tools() -> list[Tool]:
    """List available Facebook/Instagram tools"""
    return [
        # Facebook Page Tools
        Tool(
            name="facebook_get_page_info",
            description="Get Facebook Page information and stats",
            inputSchema={
                "type": "object",
                "properties": {}
            }
        ),
        Tool(
            name="facebook_get_posts",
            description="Get recent posts from Facebook Page",
            inputSchema={
                "type": "object",
                "properties": {
                    "limit": {"type": "integer", "description": "Number of posts to retrieve", "default": 25},
                    "since": {"type": "string", "description": "Start date (ISO 8601)"},
                    "until": {"type": "string", "description": "End date (ISO 8601)"}
                }
            }
        ),
        Tool(
            name="facebook_create_post",
            description="Create a new post on Facebook Page",
            inputSchema={
                "type": "object",
                "properties": {
                    "message": {"type": "string", "description": "Post message/text"},
                    "link": {"type": "string", "description": "URL to share"},
                    "photo_url": {"type": "string", "description": "URL of photo to attach"},
                    "published": {"type": "boolean", "description": "Publish immediately", "default": True}
                },
                "required": ["message"]
            }
        ),
        Tool(
            name="facebook_delete_post",
            description="Delete a Facebook Page post",
            inputSchema={
                "type": "object",
                "properties": {
                    "post_id": {"type": "string", "description": "Post ID to delete"}
                },
                "required": ["post_id"]
            }
        ),
        Tool(
            name="facebook_schedule_post",
            description="Schedule a post for future publishing",
            inputSchema={
                "type": "object",
                "properties": {
                    "message": {"type": "string", "description": "Post message"},
                    "scheduled_time": {"type": "string", "description": "Schedule time (YYYY-MM-DD HH:MM:SS)"},
                    "link": {"type": "string", "description": "URL to share"},
                    "photo_url": {"type": "string", "description": "Photo URL"}
                },
                "required": ["message", "scheduled_time"]
            }
        ),
        Tool(
            name="facebook_get_scheduled_posts",
            description="Get all scheduled posts",
            inputSchema={
                "type": "object",
                "properties": {}
            }
        ),
        # Instagram Tools
        Tool(
            name="instagram_get_account_info",
            description="Get Instagram Business Account information",
            inputSchema={
                "type": "object",
                "properties": {}
            }
        ),
        Tool(
            name="instagram_get_media",
            description="Get recent media from Instagram account",
            inputSchema={
                "type": "object",
                "properties": {
                    "limit": {"type": "integer", "description": "Number of media items", "default": 25}
                }
            }
        ),
        Tool(
            name="instagram_create_media",
            description="Create and publish Instagram media (image/video)",
            inputSchema={
                "type": "object",
                "properties": {
                    "caption": {"type": "string", "description": "Media caption"},
                    "image_url": {"type": "string", "description": "Image URL to publish"},
                    "video_url": {"type": "string", "description": "Video URL to publish"},
                    "media_type": {"type": "string", "enum": ["IMAGE", "VIDEO", "CAROUSEL"], "default": "IMAGE"}
                },
                "required": ["caption"]
            }
        ),
        Tool(
            name="instagram_get_insights",
            description="Get Instagram Business Account insights/analytics",
            inputSchema={
                "type": "object",
                "properties": {
                    "metric": {"type": "string", "description": "Specific metric name"},
                    "period": {"type": "string", "enum": ["day", "week", "month", "lifetime"], "default": "day"}
                }
            }
        ),
        # Engagement Tools
        Tool(
            name="facebook_get_conversations",
            description="Get conversations (messages and comments) from Page",
            inputSchema={
                "type": "object",
                "properties": {
                    "limit": {"type": "integer", "description": "Number of conversations", "default": 25}
                }
            }
        ),
        Tool(
            name="facebook_get_post_comments",
            description="Get comments on a specific post",
            inputSchema={
                "type": "object",
                "properties": {
                    "post_id": {"type": "string", "description": "Post ID"},
                    "limit": {"type": "integer", "description": "Number of comments", "default": 50}
                },
                "required": ["post_id"]
            }
        ),
        Tool(
            name="facebook_create_comment",
            description="Create a comment on a post",
            inputSchema={
                "type": "object",
                "properties": {
                    "object_id": {"type": "string", "description": "Post or object ID"},
                    "message": {"type": "string", "description": "Comment text"}
                },
                "required": ["object_id", "message"]
            }
        ),
        Tool(
            name="facebook_like_object",
            description="Like a post or comment",
            inputSchema={
                "type": "object",
                "properties": {
                    "object_id": {"type": "string", "description": "Post or comment ID"}
                },
                "required": ["object_id"]
            }
        ),
        # Analytics Tools
        Tool(
            name="facebook_get_page_insights",
            description="Get Facebook Page insights/analytics",
            inputSchema={
                "type": "object",
                "properties": {
                    "metrics": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "List of metric names"
                    },
                    "since": {"type": "string", "description": "Start date (YYYY-MM-DD)"},
                    "until": {"type": "string", "description": "End date (YYYY-MM-DD)"}
                }
            }
        ),
        Tool(
            name="facebook_get_post_insights",
            description="Get insights for a specific post",
            inputSchema={
                "type": "object",
                "properties": {
                    "post_id": {"type": "string", "description": "Post ID"}
                },
                "required": ["post_id"]
            }
        ),
        Tool(
            name="facebook_generate_engagement_report",
            description="Generate comprehensive engagement report for the last N days",
            inputSchema={
                "type": "object",
                "properties": {
                    "days": {"type": "integer", "description": "Number of days", "default": 7, "minimum": 1, "maximum": 90}
                }
            }
        )
    ]


@app.call_tool()
async def call_tool(name: str, arguments: dict) -> list[TextContent]:
    """Execute Facebook/Instagram tool"""
    try:
        result = None
        
        if name == "facebook_get_page_info":
            result = facebook_client.get_page_info()
            
        elif name == "facebook_get_posts":
            limit = arguments.get('limit', 25)
            since = arguments.get('since')
            until = arguments.get('until')
            result = facebook_client.get_page_posts(limit, since, until)
            
        elif name == "facebook_create_post":
            message = arguments.get('message')
            link = arguments.get('link')
            photo_url = arguments.get('photo_url')
            published = arguments.get('published', True)
            
            post_result = facebook_client.create_page_post(message, link, photo_url, published)
            result = {"success": True, "post_id": post_result.get('id')}
            
        elif name == "facebook_delete_post":
            post_id = arguments.get('post_id')
            success = facebook_client.delete_page_post(post_id)
            result = {"success": success}
            
        elif name == "facebook_schedule_post":
            message = arguments.get('message')
            scheduled_time = arguments.get('scheduled_time')
            link = arguments.get('link')
            photo_url = arguments.get('photo_url')
            
            schedule_result = facebook_client.schedule_page_post(message, scheduled_time, link, photo_url)
            result = {"success": True, "scheduled_post_id": schedule_result.get('id')}
            
        elif name == "facebook_get_scheduled_posts":
            result = facebook_client.get_scheduled_posts()
            
        elif name == "instagram_get_account_info":
            result = facebook_client.get_instagram_account_info()
            
        elif name == "instagram_get_media":
            limit = arguments.get('limit', 25)
            result = facebook_client.get_instagram_media(limit)
            
        elif name == "instagram_create_media":
            caption = arguments.get('caption')
            image_url = arguments.get('image_url')
            video_url = arguments.get('video_url')
            media_type = arguments.get('media_type', 'IMAGE')
            
            # Step 1: Create container
            container = facebook_client.create_instagram_media_container(
                caption, media_type, image_url, video_url
            )
            
            # Step 2: Publish
            publish_result = facebook_client.publish_instagram_media(container['id'])
            result = {"success": True, "media_id": publish_result.get('id')}
            
        elif name == "instagram_get_insights":
            metric = arguments.get('metric')
            period = arguments.get('period', 'day')
            result = facebook_client.get_instagram_insights(metric, period)
            
        elif name == "facebook_get_conversations":
            limit = arguments.get('limit', 25)
            result = facebook_client.get_page_conversations(limit)
            
        elif name == "facebook_get_post_comments":
            post_id = arguments.get('post_id')
            limit = arguments.get('limit', 50)
            result = facebook_client.get_post_comments(post_id, limit)
            
        elif name == "facebook_create_comment":
            object_id = arguments.get('object_id')
            message = arguments.get('message')
            comment_result = facebook_client.create_comment(object_id, message)
            result = {"success": True, "comment_id": comment_result.get('id')}
            
        elif name == "facebook_like_object":
            object_id = arguments.get('object_id')
            success = facebook_client.like_object(object_id)
            result = {"success": success}
            
        elif name == "facebook_get_page_insights":
            metrics = arguments.get('metrics')
            since = arguments.get('since')
            until = arguments.get('until')
            result = facebook_client.get_page_insights(metrics, since, until)
            
        elif name == "facebook_get_post_insights":
            post_id = arguments.get('post_id')
            result = facebook_client.get_post_insights(post_id)
            
        elif name == "facebook_generate_engagement_report":
            days = arguments.get('days', 7)
            result = facebook_client.generate_engagement_report(days)
        
        else:
            return [TextContent(type="text", text=f"Unknown tool: {name}")]
        
        return [TextContent(type="text", text=json.dumps(result, indent=2, default=str))]
        
    except Exception as e:
        logger.error(f"Tool execution error: {e}")
        return [TextContent(type="text", text=f"Error: {str(e)}")]


async def main():
    """Run the MCP server"""
    logger.info("Starting Facebook/Instagram MCP Server...")
    
    # Verify token on startup
    try:
        page_info = facebook_client.get_page_info()
        logger.info(f"Connected to Facebook Page: {page_info.get('name', 'Unknown')}")
    except Exception as e:
        logger.warning(f"Could not verify Facebook connection: {e}")
    
    async with stdio_server() as (read_stream, write_stream):
        await app.run(
            read_stream,
            write_stream,
            app.create_initialization_options()
        )


if __name__ == "__main__":
    asyncio.run(main())
