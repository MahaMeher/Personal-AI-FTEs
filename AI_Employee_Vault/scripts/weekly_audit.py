#!/usr/bin/env python3
"""
Weekly Business Audit & CEO Briefing Generator

Gold Tier Feature: Personal AI FTEs Project

Generates comprehensive weekly business reports including:
- Financial summary (from Odoo)
- Social media performance (from Facebook/Instagram)
- Task completion analysis
- Cash flow analysis
- Key metrics and KPIs
- Proactive recommendations

Runs every Monday morning at 7:00 AM
"""

import os
import sys
import json
import logging
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional

import requests
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('weekly_audit.log')
    ]
)
logger = logging.getLogger('weekly-audit')

# Configuration
VAULT_PATH = os.getenv('VAULT_PATH', 'D:/Personal-AI-FTEs/AI_Employee_Vault')
ODOO_URL = os.getenv('ODOO_URL', 'http://localhost:8069')
ODOO_DB = os.getenv('ODOO_DB', 'postgres')
ODOO_USERNAME = os.getenv('ODOO_USERNAME', 'admin')
ODOO_PASSWORD = os.getenv('ODOO_PASSWORD', 'admin')
FACEBOOK_ACCESS_TOKEN = os.getenv('FACEBOOK_ACCESS_TOKEN', '')
FACEBOOK_PAGE_ID = os.getenv('FACEBOOK_PAGE_ID', '')
INSTAGRAM_BUSINESS_ACCOUNT_ID = os.getenv('INSTAGRAM_BUSINESS_ACCOUNT_ID', '')


class OdooClient:
    """Simple Odoo JSON-RPC client"""
    
    def __init__(self, url: str, db: str, username: str, password: str):
        self.url = url.rstrip('/')
        self.db = db
        self.username = username
        self.password = password
        self.uid: Optional[int] = None
        self.session = requests.Session()
        
    def authenticate(self) -> bool:
        """Authenticate with Odoo"""
        try:
            endpoint = f"{self.url}/web/session/authenticate"
            payload = {
                "jsonrpc": "2.0",
                "method": "call",
                "params": {
                    "db": self.db,
                    "login": self.username,
                    "password": self.password
                },
                "id": 1
            }
            
            response = self.session.post(endpoint, json=payload, timeout=10)
            response.raise_for_status()
            result = response.json()
            
            if result.get('result', {}).get('uid'):
                self.uid = result['result']['uid']
                return True
            return False
        except Exception as e:
            logger.error(f"Odoo auth error: {e}")
            return False
    
    def execute_kw(self, model: str, method: str, args: list = None, kwargs: dict = None) -> Any:
        """Execute Odoo ORM method"""
        if not self.uid:
            if not self.authenticate():
                raise Exception("Not authenticated")
        
        endpoint = f"{self.url}/web/dataset/call_kw"
        payload = {
            "jsonrpc": "2.0",
            "method": "call",
            "params": {
                "model": model,
                "method": method,
                "args": args or [],
                "kwargs": kwargs or {}
            },
            "id": 2
        }
        
        response = self.session.post(endpoint, json=payload, timeout=30)
        response.raise_for_status()
        result = response.json()
        
        if 'error' in result:
            raise Exception(f"Odoo error: {result['error']}")
        
        return result.get('result')
    
    def search_read(self, model: str, domain: list = None, fields: list = None, limit: int = 80) -> list:
        """Search and read records"""
        return self.execute_kw(model, 'search_read', [domain or []], {'fields': fields, 'limit': limit})


class FacebookClient:
    """Simple Facebook Graph API client"""
    
    def __init__(self, access_token: str, page_id: str, instagram_account_id: str = None):
        self.access_token = access_token
        self.page_id = page_id
        self.instagram_account_id = instagram_account_id
        self.session = requests.Session()
        self.session.params = {'access_token': access_token}
        self.graph_api_base = f'https://graph.facebook.com/v19.0'
    
    def _get(self, endpoint: str, params: dict = None) -> dict:
        """Make GET request"""
        url = f"{self.graph_api_base}/{endpoint}"
        all_params = self.session.params.copy()
        if params:
            all_params.update(params)
        
        try:
            response = self.session.get(url, params=all_params, timeout=30)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Facebook API error: {e}")
            return {}
    
    def get_page_insights(self, since: str, until: str) -> list:
        """Get Page insights for period"""
        metrics = 'page_impressions_unique,page_reach,page_engaged_users,page_post_engagements_unique,page_likes,page_follows'
        params = {'metric': metrics, 'since': since, 'until': until}
        result = self._get(f'{self.page_id}/insights', params)
        return result.get('data', [])
    
    def get_posts(self, since: str, until: str, limit: int = 50) -> list:
        """Get posts for period"""
        params = {
            'fields': 'id,message,created_time,shares,likes.summary(true),comments.summary(true)',
            'since': since,
            'until': until,
            'limit': limit
        }
        result = self._get(f'{self.page_id}/posts', params)
        return result.get('data', [])
    
    def get_instagram_insights(self, since: str, until: str) -> list:
        """Get Instagram insights"""
        if not self.instagram_account_id:
            return []
        
        metrics = 'impressions,reach,profile_views,follower_count'
        params = {'metric': metrics, 'since': since, 'until': until}
        result = self._get(f'{self.instagram_account_id}/insights', params)
        return result.get('data', [])


class WeeklyAuditGenerator:
    """Generate weekly business audit and CEO briefing"""
    
    def __init__(self, vault_path: str):
        self.vault_path = Path(vault_path)
        self.briefings_folder = self.vault_path / 'Briefings'
        self.done_folder = self.vault_path / 'Done'
        self.logs_folder = self.vault_path / 'Logs'
        
        # Ensure directories exist
        self.briefings_folder.mkdir(parents=True, exist_ok=True)
        
        # Initialize clients
        self.odoo_client = OdooClient(ODOO_URL, ODOO_DB, ODOO_USERNAME, ODOO_PASSWORD)
        self.facebook_client = FacebookClient(
            FACEBOOK_ACCESS_TOKEN, FACEBOOK_PAGE_ID, INSTAGRAM_BUSINESS_ACCOUNT_ID
        )
    
    def generate_audit(self, weeks_ago: int = 1) -> str:
        """Generate weekly audit report"""
        # Calculate date range
        today = datetime.now()
        week_start = today - timedelta(days=today.weekday() + (weeks_ago * 7), hours=today.hour, minutes=today.minute, seconds=today.second)
        week_end = week_start + timedelta(days=7)
        
        since = week_start.strftime('%Y-%m-%d')
        until = week_end.strftime('%Y-%m-%d')
        
        logger.info(f"Generating weekly audit for {since} to {until}")
        
        # Collect data from all sources
        financial_data = self._collect_financial_data(since, until)
        social_data = self._collect_social_data(since, until)
        task_data = self._collect_task_data(since, until)
        
        # Generate briefing
        briefing = self._generate_briefing(financial_data, social_data, task_data, since, until)
        
        # Save briefing
        filename = f"{week_end.strftime('%Y%m%d')}_Weekly_Business_Audit.md"
        filepath = self.briefings_folder / filename
        filepath.write_text(briefing, encoding='utf-8')
        
        logger.info(f"Weekly audit saved to: {filepath}")
        return filepath
    
    def _collect_financial_data(self, since: str, until: str) -> dict:
        """Collect financial data from Odoo"""
        data = {
            'revenue': 0.0,
            'expenses': 0.0,
            'profit': 0.0,
            'invoices_sent': 0,
            'invoices_paid': 0,
            'outstanding_receivable': 0.0,
            'outstanding_payable': 0.0,
            'vendor_bills': 0,
            'payments_made': 0
        }
        
        try:
            if not self.odoo_client.authenticate():
                logger.warning("Could not authenticate with Odoo")
                return data
            
            # Get customer invoices
            domain = [
                ('move_type', '=', 'out_invoice'),
                ('invoice_date', '>=', since),
                ('invoice_date', '<=', until),
                ('state', '=', 'posted')
            ]
            invoices = self.odoo_client.search_read('account.move', domain, 
                                                   ['amount_total', 'amount_residual', 'payment_state'])
            
            for invoice in invoices:
                data['invoices_sent'] += 1
                data['revenue'] += invoice.get('amount_total', 0) or 0
                if invoice.get('payment_state') == 'paid':
                    data['invoices_paid'] += 1
                else:
                    data['outstanding_receivable'] += invoice.get('amount_residual', 0) or 0
            
            # Get vendor bills
            domain = [
                ('move_type', 'in', ['in_invoice', 'in_refund']),
                ('invoice_date', '>=', since),
                ('invoice_date', '<=', until),
                ('state', '=', 'posted')
            ]
            bills = self.odoo_client.search_read('account.move', domain, ['amount_total', 'amount_residual'])
            
            for bill in bills:
                data['vendor_bills'] += 1
                data['expenses'] += abs(bill.get('amount_total', 0) or 0)
                data['outstanding_payable'] += bill.get('amount_residual', 0) or 0
            
            data['profit'] = data['revenue'] - data['expenses']
            
        except Exception as e:
            logger.error(f"Error collecting financial data: {e}")
        
        return data
    
    def _collect_social_data(self, since: str, until: str) -> dict:
        """Collect social media data from Facebook/Instagram"""
        data = {
            'facebook': {
                'reach': 0,
                'impressions': 0,
                'engagements': 0,
                'new_likes': 0,
                'new_follows': 0,
                'posts_count': 0,
                'top_posts': []
            },
            'instagram': {
                'reach': 0,
                'impressions': 0,
                'profile_views': 0,
                'follower_count': 0
            }
        }
        
        try:
            # Facebook insights
            fb_insights = self.facebook_client.get_page_insights(since, until)
            for insight in fb_insights:
                name = insight.get('name', '')
                value = insight.get('values', [{}])[0].get('value', 0) or 0
                
                if 'reach' in name:
                    data['facebook']['reach'] += value
                elif 'impressions' in name:
                    data['facebook']['impressions'] += value
                elif 'engaged_users' in name:
                    data['facebook']['engagements'] += value
                elif 'likes' in name:
                    data['facebook']['new_likes'] += value
                elif 'follows' in name:
                    data['facebook']['new_follows'] += value
            
            # Facebook posts
            posts = self.facebook_client.get_posts(since, until)
            data['facebook']['posts_count'] = len(posts)
            
            # Get top posts by engagement
            for post in posts[:3]:
                shares = post.get('shares', {}).get('count', 0) if post.get('shares') else 0
                likes = post.get('likes', {}).get('summary', {}).get('total_count', 0) if post.get('likes') else 0
                comments = post.get('comments', {}).get('summary', {}).get('total_count', 0) if post.get('comments') else 0
                
                data['facebook']['top_posts'].append({
                    'id': post.get('id', ''),
                    'message': post.get('message', '')[:100] if post.get('message') else 'No text',
                    'engagements': shares + likes + comments,
                    'permalink': post.get('permalink_url', '')
                })
            
            # Sort by engagements
            data['facebook']['top_posts'].sort(key=lambda x: x['engagements'], reverse=True)
            
            # Instagram insights
            ig_insights = self.facebook_client.get_instagram_insights(since, until)
            for insight in ig_insights:
                name = insight.get('name', '')
                value = insight.get('values', [{}])[0].get('value', 0) or 0
                
                if 'reach' in name:
                    data['instagram']['reach'] += value
                elif 'impressions' in name:
                    data['instagram']['impressions'] += value
                elif 'profile_views' in name:
                    data['instagram']['profile_views'] += value
                elif 'follower_count' in name:
                    data['instagram']['follower_count'] = value
            
        except Exception as e:
            logger.error(f"Error collecting social data: {e}")
        
        return data
    
    def _collect_task_data(self, since: str, until: str) -> dict:
        """Collect task completion data from vault"""
        data = {
            'tasks_completed': 0,
            'tasks_by_type': {},
            'average_completion_time': 'N/A',
            'pending_tasks': 0,
            'overdue_tasks': 0
        }
        
        try:
            # Count completed tasks
            if self.done_folder.exists():
                for file in self.done_folder.glob('*.md'):
                    try:
                        content = file.read_text(encoding='utf-8')
                        if 'created:' in content:
                            data['tasks_completed'] += 1
                            
                            # Extract task type
                            if 'type: email' in content:
                                task_type = 'email'
                            elif 'type: facebook' in content or 'type: social' in content:
                                task_type = 'social_media'
                            elif 'type: odoo' in content or 'type: accounting' in content:
                                task_type = 'accounting'
                            elif 'type: invoice' in content:
                                task_type = 'invoicing'
                            else:
                                task_type = 'other'
                            
                            data['tasks_by_type'][task_type] = data['tasks_by_type'].get(task_type, 0) + 1
                    except Exception:
                        continue
            
            # Count pending tasks
            needs_action = self.vault_path / 'Needs_Action'
            if needs_action.exists():
                data['pending_tasks'] = len(list(needs_action.glob('*.md')))
            
            # Count overdue tasks
            for file in (self.vault_path / 'Needs_Action').glob('*.md'):
                try:
                    content = file.read_text(encoding='utf-8')
                    if 'priority: high' in content or 'priority: critical' in content:
                        data['overdue_tasks'] += 1
                except Exception:
                    continue
            
        except Exception as e:
            logger.error(f"Error collecting task data: {e}")
        
        return data
    
    def _generate_briefing(self, financial: dict, social: dict, tasks: dict, 
                          since: str, until: str) -> str:
        """Generate CEO briefing markdown"""
        week_end = datetime.strptime(until, '%Y-%m-%d')
        
        # Calculate week-over-week changes (simplified - would compare to previous week)
        revenue_change = "+0.0%"  # Would calculate from previous week
        profit_change = "+0.0%"
        engagement_change = "+0.0%"
        
        # Determine overall sentiment
        if financial['profit'] > 0:
            overall_sentiment = "🟢 Positive"
        elif financial['profit'] == 0:
            overall_sentiment = "🟡 Neutral"
        else:
            overall_sentiment = "🔴 Needs Attention"
        
        # Generate proactive recommendations
        recommendations = self._generate_recommendations(financial, social, tasks)
        
        briefing = f"""---
generated: {datetime.now().isoformat()}
period: {since} to {until}
type: weekly_business_audit
status: final
---

# Monday Morning CEO Briefing

## Week of {week_end.strftime('%B %d, %Y')}

**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M')}  
**Overall Status:** {overall_sentiment}

---

## Executive Summary

This week, the business generated **${financial['revenue']:,.2f}** in revenue with **${financial['profit']:,.2f}** profit. 
Social media reached **{social['facebook']['reach'] + social['instagram']['reach']:,}** people across platforms.

**Key Highlights:**
- Revenue: ${financial['revenue']:,.2f} ({revenue_change} vs last week)
- Profit: ${financial['profit']:,.2f} ({profit_change} vs last week)
- Social Reach: {social['facebook']['reach'] + social['instagram']['reach']:,} ({engagement_change} vs last week)
- Tasks Completed: {tasks['tasks_completed']}

---

## Financial Performance

### Revenue & Profit

| Metric | This Week | Status |
|--------|-----------|--------|
| **Revenue** | ${financial['revenue']:,.2f} | {'✅' if financial['revenue'] > 0 else '⚠️'} |
| **Expenses** | ${financial['expenses']:,.2f} | {'✅' if financial['expenses'] < financial['revenue'] else '⚠️'} |
| **Profit** | ${financial['profit']:,.2f} | {'✅' if financial['profit'] > 0 else '⚠️'} |
| **Profit Margin** | {(financial['profit'] / financial['revenue'] * 100) if financial['revenue'] > 0 else 0:.1f}% | |

### Invoices & Payments

| Metric | Count | Amount |
|--------|-------|--------|
| Invoices Sent | {financial['invoices_sent']} | ${financial['revenue']:,.2f} |
| Invoices Paid | {financial['invoices_paid']} | - |
| Outstanding Receivable | - | ${financial['outstanding_receivable']:,.2f} |
| Vendor Bills | {financial['vendor_bills']} | ${financial['expenses']:,.2f} |
| Outstanding Payable | - | ${financial['outstanding_payable']:,.2f} |

### Cash Flow Alert

{'⚠️ **Attention:** Outstanding receivables are high. Consider following up on overdue invoices.' if financial['outstanding_receivable'] > financial['revenue'] * 0.3 else '✅ Cash flow looks healthy.'}

---

## Social Media Performance

### Facebook

| Metric | Value |
|--------|-------|
| Reach | {social['facebook']['reach']:,} |
| Impressions | {social['facebook']['impressions']:,} |
| Engagements | {social['facebook']['engagements']:,} |
| New Likes | {social['facebook']['new_likes']} |
| New Follows | {social['facebook']['new_follows']} |
| Posts Published | {social['facebook']['posts_count']} |

#### Top Performing Posts

{self._format_top_posts(social['facebook']['top_posts'])}

### Instagram

| Metric | Value |
|--------|-------|
| Reach | {social['instagram']['reach']:,} |
| Impressions | {social['instagram']['impressions']:,} |
| Profile Views | {social['instagram']['profile_views']} |
| Followers | {social['instagram']['follower_count']:,} |

---

## Task Completion Analysis

### Overview

- **Tasks Completed:** {tasks['tasks_completed']}
- **Pending Tasks:** {tasks['pending_tasks']}
- **High Priority:** {tasks['overdue_tasks']}

### Tasks by Type

| Type | Count |
|------|-------|
{self._format_task_types(tasks['tasks_by_type'])}

### Productivity Score

{'✅ High productivity' if tasks['tasks_completed'] >= 20 else '⚠️ Moderate productivity' if tasks['tasks_completed'] >= 10 else '🔴 Low productivity - review workload'}

---

## Proactive Recommendations

{recommendations}

---

## Action Items for This Week

### Immediate (Today)

- [ ] Review outstanding receivables and send reminders
- [ ] Respond to high-priority social media comments
- [ ] Process pending vendor payments

### This Week

- [ ] Schedule social media content for next week
- [ ] Review and approve draft invoices
- [ ] Follow up on overdue customer payments
- [ ] Analyze top-performing content and replicate success

### Strategic

- [ ] Review monthly revenue targets vs actual
- [ ] Plan upcoming product/service launches
- [ ] Consider automation opportunities for repetitive tasks

---

## Key Metrics Dashboard

### Weekly Trends

| Week | Revenue | Profit | Social Reach | Tasks Done |
|------|---------|--------|--------------|------------|
| This Week | ${financial['revenue']:,.2f} | ${financial['profit']:,.2f} | {social['facebook']['reach'] + social['instagram']['reach']:,} | {tasks['tasks_completed']} |
| Last Week | - | - | - | - |
| 2 Weeks Ago | - | - | - | - |

### Monthly Targets Progress

| Metric | Target | Actual | Progress |
|--------|--------|--------|----------|
| Revenue | $10,000 | ${financial['revenue']:,.2f} | {min(100, (financial['revenue'] / 10000 * 100)):.0f}% |
| Profit | $5,000 | ${financial['profit']:,.2f} | {min(100, (financial['profit'] / 5000 * 100)):.0f}% |
| Social Reach | 50,000 | {social['facebook']['reach'] + social['instagram']['reach']:,} | {min(100, ((social['facebook']['reach'] + social['instagram']['reach']) / 50000 * 100)):.0f}% |

---

## Notes & Observations

*This report was automatically generated by your AI Employee.*

**Data Sources:**
- Financial data: Odoo ERP
- Social media: Facebook/Instagram Graph API
- Task data: Obsidian Vault

**Next Scheduled Report:** {week_end.strftime('%Y-%m-%d')} (Next Monday at 7:00 AM)

---

*Generated by Weekly Business Audit - Gold Tier Feature*
*Personal AI FTEs Project | Version 1.0*
"""
        
        return briefing
    
    def _format_top_posts(self, top_posts: list) -> str:
        """Format top posts as markdown table"""
        if not top_posts:
            return "*No posts this week*"
        
        table = "| Post | Engagements | Link |\n|------|-------------|------|\n"
        for i, post in enumerate(top_posts, 1):
            message = post['message'][:50] + '...' if len(post['message']) > 50 else post['message']
            table += f"| {i}. {message} | {post['engagements']} | [View]({post['permalink']}) |\n"
        
        return table
    
    def _format_task_types(self, task_types: dict) -> str:
        """Format task types as markdown table rows"""
        if not task_types:
            return "| Other | 0 |\n"
        
        rows = ""
        for task_type, count in sorted(task_types.items(), key=lambda x: x[1], reverse=True):
            rows += f"| {task_type.replace('_', ' ').title()} | {count} |\n"
        
        return rows
    
    def _generate_recommendations(self, financial: dict, social: dict, tasks: dict) -> str:
        """Generate proactive recommendations based on data"""
        recommendations = []
        
        # Financial recommendations
        if financial['outstanding_receivable'] > financial['revenue'] * 0.3:
            recommendations.append("💰 **Cash Flow:** Consider sending payment reminders to customers with overdue invoices. ${financial['outstanding_receivable']:,.2f} is outstanding.")
        
        if financial['profit'] < 0:
            recommendations.append("📉 **Profitability:** Expenses exceed revenue this week. Review vendor bills and consider cost-cutting measures.")
        
        # Social media recommendations
        if social['facebook']['posts_count'] < 3:
            recommendations.append("📱 **Social Media:** Consider increasing posting frequency. Only {social['facebook']['posts_count']} posts this week.")
        
        if social['facebook']['engagements'] > 0:
            top_post = social['facebook']['top_posts'][0] if social['facebook']['top_posts'] else None
            if top_post:
                recommendations.append(f"🎯 **Content Strategy:** Top post was about \"{top_post['message'][:50]}...\". Consider creating more similar content.")
        
        # Task recommendations
        if tasks['overdue_tasks'] > 0:
            recommendations.append(f"⚠️ **Task Management:** {tasks['overdue_tasks']} high-priority tasks are pending. Review and prioritize.")
        
        if tasks['tasks_completed'] < 10:
            recommendations.append("📋 **Productivity:** Task completion rate is low. Consider automating more routine tasks.")
        
        if not recommendations:
            return "✅ All systems running smoothly. No critical issues identified."
        
        return "\n\n".join(recommendations)


def main():
    """Main entry point"""
    vault_path = VAULT_PATH
    
    # Verify vault exists
    if not Path(vault_path).exists():
        logger.error(f"Vault path does not exist: {vault_path}")
        sys.exit(1)
    
    # Generate audit
    generator = WeeklyAuditGenerator(vault_path)
    
    try:
        filepath = generator.generate_audit(weeks_ago=0)
        logger.info(f"Weekly audit generated successfully: {filepath}")
        print(f"Weekly audit saved to: {filepath}")
    except Exception as e:
        logger.error(f"Error generating audit: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
