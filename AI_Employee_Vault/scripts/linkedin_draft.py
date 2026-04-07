"""
LinkedIn Post Draft Creator

Automatically creates LinkedIn post drafts based on Business_Goals.md
and recent accomplishments. Posts are created for human approval.

Silver Tier Requirement: "Automatically Post on LinkedIn about business to generate sales"

Usage:
    python scripts/linkedin_draft.py [--topic "topic"]
    python scripts/linkedin_draft.py --auto  # Auto-generate from Business_Goals.md
"""

import sys
import re
import random
from pathlib import Path
from datetime import datetime, timedelta
from typing import List, Dict, Optional


class LinkedInDraftCreator:
    """Create LinkedIn post drafts for approval."""
    
    def __init__(self, vault_path: str):
        self.vault_path = Path(vault_path)
        self.business_goals = self.vault_path / 'Business_Goals.md'
        self.done_dir = self.vault_path / 'Done'
        self.pending_approval = self.vault_path / 'Pending_Approval'
        self.dashboard = self.vault_path / 'Dashboard.md'
        
        self.pending_approval.mkdir(parents=True, exist_ok=True)
        
        # Post templates for different purposes
        self.templates = {
            'business_update': self._business_update_template,
            'milestone': self._milestone_template,
            'service_offering': self._service_offering_template,
            'client_success': self._client_success_template,
            'industry_insight': self._industry_insight_template,
        }
    
    def _business_update_template(self, goals: Dict) -> str:
        """Generate business update post."""
        revenue_goal = goals.get('revenue_goal', '$10,000')
        return f'''🚀 Business Update

We're working towards our Q1 goal of {revenue_goal}/month!

Current focus areas:
✅ Delivering exceptional value to clients
✅ Building innovative AI automation solutions
✅ Helping businesses streamline operations

Interested in learning how we can help your business? Let's connect!

#Business #AI #Automation #Growth'''
    
    def _milestone_template(self, goals: Dict) -> str:
        """Generate milestone celebration post."""
        return f'''🎉 Milestone Achieved!

Another step forward in our journey!

We believe in:
✓ Continuous improvement
✓ Client-first approach
✓ Innovation in every project

Thank you to our amazing network for the support!

#Milestone #Progress #BusinessGrowth #AI'''
    
    def _service_offering_template(self, goals: Dict) -> str:
        """Generate service offering post."""
        return f'''💼 Now Offering: AI Employee Solutions

Transform your business with autonomous AI agents that work 24/7!

Our services:
📧 Email automation & monitoring
📱 Social media management
📊 Business intelligence & reporting
⚙️ Custom workflow automation

Ready to automate your business? Let's talk!

#AI #Automation #BusinessSolutions #Tech'''
    
    def _client_success_template(self, goals: Dict) -> str:
        """Generate client success story post."""
        return f'''⭐ Client Success Story

Another happy client! 

We helped them:
→ Reduce manual work by 80%
→ Get faster response times
→ Focus on what matters most

Your success is our success!

#ClientSuccess #Automation #AI #Results'''
    
    def _industry_insight_template(self, goals: Dict) -> str:
        """Generate industry insight post."""
        insights = [
            "Did you know? AI automation can reduce operational costs by up to 60%!",
            "The future of business is autonomous. Are you ready?",
            "Smart businesses are using AI employees to scale without increasing headcount.",
            "Automation isn't about replacing humans - it's about empowering them.",
        ]
        return f'''💡 Industry Insight

{random.choice(insights)}

Stay ahead of the curve!

#IndustryInsights #AI #FutureOfWork #Innovation'''
    
    def load_business_goals(self) -> Dict:
        """Load business goals from file."""
        goals = {
            'revenue_goal': '$10,000',
            'projects': [],
            'metrics': {}
        }
        
        if not self.business_goals.exists():
            return goals
        
        try:
            content = self.business_goals.read_text(encoding='utf-8')
            
            # Extract revenue goal
            revenue_match = re.search(r'Monthly goal:?\s*\$?(\d+(?:,\d+)?)', content)
            if revenue_match:
                goals['revenue_goal'] = f"${revenue_match.group(1).replace(',', '')}"
            
            # Extract active projects
            projects_section = re.search(r'### Active Projects\s*\n(.*?)(?:###|$)', content, re.DOTALL)
            if projects_section:
                projects = re.findall(r'\d+\.\s*(.+)', projects_section.group(1))
                goals['projects'] = [p.strip() for p in projects]
            
            # Extract metrics
            metrics_match = re.findall(r'\|\s*(.+?)\s*\|\s*(.+?)\s*\|', content)
            goals['metrics'] = {m[0]: m[1] for m in metrics_match}
            
        except Exception as e:
            print(f"Error loading business goals: {e}")
        
        return goals
    
    def get_recent_accomplishments(self, days: int = 7) -> List[str]:
        """Get recent accomplishments from Done folder."""
        accomplishments = []
        
        if not self.done_dir.exists():
            return accomplishments
        
        cutoff = datetime.now() - timedelta(days=days)
        
        for file in self.done_dir.glob('*.md'):
            try:
                mtime = datetime.fromtimestamp(file.stat().st_mtime)
                if mtime >= cutoff:
                    # Extract meaningful name
                    name = file.stem.replace('FILE_', '').replace('_', ' ').title()
                    accomplishments.append(name)
            except Exception:
                continue
        
        return accomplishments[:5]  # Limit to 5
    
    def create_draft(self, topic: str = None) -> Optional[Path]:
        """
        Create a LinkedIn post draft.
        
        Args:
            topic: Optional topic override
            
        Returns:
            Path to created draft file
        """
        # Load business goals
        goals = self.load_business_goals()
        
        # Get recent accomplishments
        accomplishments = self.get_recent_accomplishments()
        
        # Determine post type
        if topic:
            post_type = topic.lower()
        elif accomplishments:
            post_type = 'milestone'
        else:
            post_type = random.choice(list(self.templates.keys()))
        
        # Generate content
        template = self.templates.get(post_type, self.templates['business_update'])
        content = template(goals)
        
        # Create draft file
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        draft_file = self.pending_approval / f'LINKEDIN_POST_{post_type}_{timestamp}.md'
        
        # Determine best posting time
        best_times = {
            'Tuesday': '10:00 AM',
            'Wednesday': '2:00 PM',
            'Thursday': '11:00 AM'
        }
        today = datetime.now().strftime('%A')
        suggested_time = best_times.get(today, '10:00 AM')
        
        draft_content = f'''---
type: linkedin_post
topic: {post_type}
created: {datetime.now().isoformat()}
status: pending_approval
requires_approval: true
post_type: {post_type}
suggested_post_time: {suggested_time}
---

# LinkedIn Post Draft

**Topic:** {post_type.replace('_', ' ').title()}  
**Created:** {datetime.now().strftime('%Y-%m-%d %H:%M')}  
**Suggested Post Time:** {suggested_time}

## Post Content

```
{content}
```

## Posting Instructions

1. Review the post content above
2. If approved, move this file to `/Approved/`
3. The AI will post to LinkedIn automatically
4. If rejected, move to `/Rejected/` with feedback

## Why This Post?

'''
        
        if post_type == 'milestone' and accomplishments:
            draft_content += f"Recent accomplishments: {', '.join(accomplishments)}\n"
        elif post_type == 'business_update':
            draft_content += f"Revenue goal: {goals['revenue_goal']}/month\n"
        elif post_type == 'service_offering':
            draft_content += "Promoting AI Employee services to generate leads\n"
        else:
            draft_content += "Engaging network with valuable content\n"
        
        draft_content += f'''
## Expected Engagement

- **Reach:** 500-1000 impressions
- **Engagement:** 20-50 likes, 5-10 comments
- **Goal:** Generate business leads

---
*To approve: Move this file to `/Approved/`*
*Auto-generated by AI Employee LinkedIn Draft Creator*
'''
        
        draft_file.write_text(draft_content, encoding='utf-8')
        
        return draft_file
    
    def create_weekly_posts(self) -> List[Path]:
        """Create a week's worth of post drafts."""
        posts = []
        
        # Different post types for variety
        post_schedule = [
            ('business_update', 'Monday'),
            ('service_offering', 'Wednesday'),
            ('industry_insight', 'Friday'),
        ]
        
        for post_type, day in post_schedule:
            draft = self.create_draft(post_type)
            if draft:
                posts.append(draft)
        
        return posts


def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(description='LinkedIn Draft Creator')
    parser.add_argument('--topic', type=str, help='Post topic')
    parser.add_argument('--auto', action='store_true', help='Auto-generate from Business_Goals.md')
    parser.add_argument('--weekly', action='store_true', help='Create week\'s worth of posts')
    parser.add_argument('--vault', type=str, help='Path to vault')
    
    args = parser.parse_args()
    
    # Get vault path
    vault_path = args.vault if args.vault else str(Path(__file__).parent.parent)
    
    creator = LinkedInDraftCreator(vault_path)
    
    print("=" * 60)
    print("AI Employee - LinkedIn Draft Creator")
    print("=" * 60)
    
    if args.weekly:
        # Create week's worth of posts
        print("\nCreating weekly post schedule...")
        posts = creator.create_weekly_posts()
        print(f"✓ Created {len(posts)} post drafts in Pending_Approval/")
        for post in posts:
            print(f"  - {post.name}")
    elif args.auto or not args.topic:
        # Auto-generate from Business_Goals.md
        print("\nAuto-generating post from Business_Goals.md...")
        draft = creator.create_draft()
        if draft:
            print(f"✓ Draft created: {draft.name}")
            print(f"  Location: Pending_Approval/{draft.name}")
            print("\nTo post:")
            print("  1. Review the draft")
            print("  2. Move to Approved/ to publish")
    else:
        # Create specific topic
        print(f"\nCreating post: {args.topic}...")
        draft = creator.create_draft(args.topic)
        if draft:
            print(f"✓ Draft created: {draft.name}")
    
    print("\n" + "=" * 60)


if __name__ == '__main__':
    main()
