#!/usr/bin/env python3
"""
Comprehensive Audit Logger

Gold Tier Feature: Personal AI FTEs Project

Provides centralized audit logging for all AI Employee actions including:
- All MCP server calls (Odoo, Facebook, Email, etc.)
- File operations (create, move, delete)
- Watcher events
- Human-in-the-loop approvals
- Task completion status

Log format follows security best practices for compliance and debugging.
"""

import os
import sys
import json
import logging
import hashlib
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, Any, List

from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configuration
VAULT_PATH = os.getenv('VAULT_PATH', 'D:/Personal-AI-FTEs/AI_Employee_Vault')
LOG_RETENTION_DAYS = int(os.getenv('LOG_RETENTION_DAYS', '90'))
ENABLE_CONSOLE_LOGGING = os.getenv('ENABLE_CONSOLE_LOGGING', 'true').lower() == 'true'


class AuditLogger:
    """Centralized audit logger for AI Employee actions"""
    
    def __init__(self, vault_path: str):
        self.vault_path = Path(vault_path)
        self.logs_folder = self.vault_path / 'Logs'
        self.audit_file = self.logs_folder / f"{datetime.now().strftime('%Y-%m-%d')}.jsonl"
        
        # Ensure logs folder exists
        self.logs_folder.mkdir(parents=True, exist_ok=True)
        
        # Setup logging
        self._setup_logging()
        
        # Log rotation - cleanup old logs
        self._cleanup_old_logs()
    
    def _setup_logging(self):
        """Setup Python logging to also write to audit log"""
        self.logger = logging.getLogger('audit-logger')
        self.logger.setLevel(logging.INFO)
        
        # Clear existing handlers
        self.logger.handlers = []
        
        # Console handler (optional)
        if ENABLE_CONSOLE_LOGGING:
            console_handler = logging.StreamHandler()
            console_handler.setLevel(logging.INFO)
            console_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            console_handler.setFormatter(console_formatter)
            self.logger.addHandler(console_handler)
    
    def _get_audit_entry(self, action_type: str, actor: str, target: str,
                         parameters: Dict = None, result: str = 'success',
                         approval_status: str = 'auto', approved_by: str = None,
                         metadata: Dict = None) -> Dict:
        """Create standardized audit log entry"""
        entry = {
            'timestamp': datetime.now().isoformat(),
            'action_type': action_type,
            'actor': actor,  # Who/what performed the action
            'target': target,  # What was acted upon
            'parameters': parameters or {},
            'result': result,  # success, failure, error
            'approval_status': approval_status,  # auto, human, pending
            'approved_by': approved_by,
            'metadata': metadata or {},
            'checksum': None  # Will be calculated
        }
        
        # Calculate checksum for integrity verification
        entry['checksum'] = self._calculate_checksum(entry)
        
        return entry
    
    def _calculate_checksum(self, entry: Dict) -> str:
        """Calculate SHA256 checksum for audit entry"""
        # Create hash of all fields except checksum
        data = {k: v for k, v in entry.items() if k != 'checksum'}
        data_str = json.dumps(data, sort_keys=True)
        return hashlib.sha256(data_str.encode()).hexdigest()
    
    def log(self, action_type: str, actor: str, target: str,
            parameters: Dict = None, result: str = 'success',
            approval_status: str = 'auto', approved_by: str = None,
            metadata: Dict = None):
        """Log an audit event"""
        entry = self._get_audit_entry(
            action_type=action_type,
            actor=actor,
            target=target,
            parameters=parameters,
            result=result,
            approval_status=approval_status,
            approved_by=approved_by,
            metadata=metadata
        )
        
        # Write to daily audit file (JSONL format)
        with open(self.audit_file, 'a', encoding='utf-8') as f:
            f.write(json.dumps(entry) + '\n')
        
        # Also log to standard logger
        self.logger.info(f"{action_type} by {actor} on {target}: {result}")
        
        return entry
    
    # Convenience methods for common actions
    
    def log_mcp_call(self, mcp_server: str, tool_name: str, parameters: Dict,
                    result: str = 'success', error: str = None):
        """Log MCP server tool call"""
        return self.log(
            action_type='mcp_tool_call',
            actor=mcp_server,
            target=tool_name,
            parameters=parameters,
            result=result,
            metadata={'error': error} if error else {}
        )
    
    def log_file_operation(self, operation: str, file_path: str, actor: str,
                          metadata: Dict = None):
        """Log file system operation"""
        return self.log(
            action_type=f'file_{operation}',  # create, move, delete, modify
            actor=actor,
            target=file_path,
            parameters={},
            result='success',
            metadata=metadata or {}
        )
    
    def log_watcher_event(self, watcher_name: str, event_type: str,
                         items_detected: int, actor: str = 'watcher'):
        """Log watcher detection event"""
        return self.log(
            action_type='watcher_event',
            actor=actor,
            target=watcher_name,
            parameters={'event_type': event_type, 'items_detected': items_detected},
            result='success'
        )
    
    def log_approval_request(self, request_id: str, action_type: str,
                            requester: str, approver: str = None,
                            status: str = 'pending'):
        """Log human-in-the-loop approval request"""
        return self.log(
            action_type='approval_request',
            actor=requester,
            target=request_id,
            parameters={'action_type': action_type},
            result='success',
            approval_status=status,
            approved_by=approver
        )
    
    def log_task_completion(self, task_id: str, actor: str,
                           iterations: int = 1, duration_seconds: float = None):
        """Log task completion (Ralph Wiggum loop)"""
        return self.log(
            action_type='task_complete',
            actor=actor,
            target=task_id,
            parameters={'iterations': iterations, 'duration_seconds': duration_seconds},
            result='success'
        )
    
    def log_email_action(self, action: str, recipient: str, subject: str,
                        actor: str, metadata: Dict = None):
        """Log email action (send, receive, draft)"""
        return self.log(
            action_type=f'email_{action}',
            actor=actor,
            target=recipient,
            parameters={'subject': subject},
            result='success',
            metadata=metadata or {}
        )
    
    def log_social_media_action(self, platform: str, action: str,
                               content: str, actor: str,
                               post_id: str = None):
        """Log social media action (post, comment, like)"""
        return self.log(
            action_type=f'social_{platform}_{action}',
            actor=actor,
            target=post_id or 'new_post',
            parameters={'content': content[:200]},  # Truncate for logging
            result='success'
        )
    
    def log_accounting_action(self, action: str, document_type: str,
                             document_id: str, amount: float = None,
                             actor: str = 'odoo-mcp'):
        """Log accounting action (invoice, payment, journal entry)"""
        return self.log(
            action_type=f'accounting_{action}',
            actor=actor,
            target=document_id,
            parameters={
                'document_type': document_type,
                'amount': amount
            },
            result='success'
        )
    
    def log_error(self, error_type: str, error_message: str,
                 actor: str, context: Dict = None):
        """Log error event"""
        return self.log(
            action_type='error',
            actor=actor,
            target=error_type,
            parameters={'error_message': error_message},
            result='error',
            metadata=context or {}
        )
    
    def _cleanup_old_logs(self):
        """Remove audit logs older than retention period"""
        try:
            cutoff = datetime.now().timestamp() - (LOG_RETENTION_DAYS * 24 * 60 * 60)
            
            for log_file in self.logs_folder.glob("*.jsonl"):
                if log_file.stat().st_mtime < cutoff:
                    log_file.unlink()
                    self.logger.info(f"Deleted old log file: {log_file.name}")
        except Exception as e:
            self.logger.error(f"Error cleaning up old logs: {e}")
    
    def get_logs_for_date(self, date: str) -> List[Dict]:
        """Get all logs for a specific date"""
        log_file = self.logs_folder / f"{date}.jsonl"
        if not log_file.exists():
            return []
        
        logs = []
        with open(log_file, 'r', encoding='utf-8') as f:
            for line in f:
                try:
                    logs.append(json.loads(line))
                except json.JSONDecodeError:
                    continue
        
        return logs
    
    def get_logs_by_actor(self, actor: str, date: str = None) -> List[Dict]:
        """Get all logs for a specific actor"""
        if date:
            logs = self.get_logs_for_date(date)
        else:
            # Get today's logs
            logs = self.get_logs_for_date(datetime.now().strftime('%Y-%m-%d'))
        
        return [log for log in logs if log.get('actor') == actor]
    
    def get_logs_by_action_type(self, action_type: str, date: str = None) -> List[Dict]:
        """Get all logs for a specific action type"""
        if date:
            logs = self.get_logs_for_date(date)
        else:
            logs = self.get_logs_for_date(datetime.now().strftime('%Y-%m-%d'))
        
        return [log for log in logs if log.get('action_type') == action_type]
    
    def generate_daily_summary(self, date: str = None) -> Dict:
        """Generate summary of all actions for a day"""
        if date is None:
            date = datetime.now().strftime('%Y-%m-%d')
        
        logs = self.get_logs_for_date(date)
        
        summary = {
            'date': date,
            'total_actions': len(logs),
            'by_actor': {},
            'by_action_type': {},
            'errors': 0,
            'approvals_required': 0,
            'approvals_granted': 0
        }
        
        for log in logs:
            # Count by actor
            actor = log.get('actor', 'unknown')
            summary['by_actor'][actor] = summary['by_actor'].get(actor, 0) + 1
            
            # Count by action type
            action_type = log.get('action_type', 'unknown')
            summary['by_action_type'][action_type] = summary['by_action_type'].get(action_type, 0) + 1
            
            # Count errors
            if log.get('result') == 'error':
                summary['errors'] += 1
            
            # Count approvals
            if log.get('approval_status') == 'pending':
                summary['approvals_required'] += 1
            elif log.get('approval_status') == 'human':
                summary['approvals_granted'] += 1
        
        return summary
    
    def verify_audit_integrity(self, date: str = None) -> bool:
        """Verify audit log integrity by checking checksums"""
        if date is None:
            date = datetime.now().strftime('%Y-%m-%d')
        
        log_file = self.logs_folder / f"{date}.jsonl"
        if not log_file.exists():
            return True  # No logs to verify
        
        with open(log_file, 'r', encoding='utf-8') as f:
            for line_num, line in enumerate(f, 1):
                try:
                    entry = json.loads(line)
                    stored_checksum = entry.pop('checksum', None)
                    calculated_checksum = hashlib.sha256(
                        json.dumps(entry, sort_keys=True).encode()
                    ).hexdigest()
                    
                    if stored_checksum != calculated_checksum:
                        self.logger.error(f"Checksum mismatch on line {line_num}")
                        return False
                except Exception as e:
                    self.logger.error(f"Error verifying line {line_num}: {e}")
                    return False
        
        self.logger.info(f"Audit log integrity verified for {date}")
        return True


# Global audit logger instance
_audit_logger: Optional[AuditLogger] = None


def get_audit_logger() -> AuditLogger:
    """Get or create global audit logger instance"""
    global _audit_logger
    if _audit_logger is None:
        vault_path = VAULT_PATH
        if not Path(vault_path).exists():
            raise Exception(f"Vault path does not exist: {vault_path}")
        _audit_logger = AuditLogger(vault_path)
    return _audit_logger


# Convenience functions for direct import
def log_mcp_call(mcp_server: str, tool_name: str, parameters: Dict,
                result: str = 'success', error: str = None):
    return get_audit_logger().log_mcp_call(mcp_server, tool_name, parameters, result, error)


def log_file_operation(operation: str, file_path: str, actor: str, metadata: Dict = None):
    return get_audit_logger().log_file_operation(operation, file_path, actor, metadata)


def log_approval_request(request_id: str, action_type: str, requester: str,
                        approver: str = None, status: str = 'pending'):
    return get_audit_logger().log_approval_request(request_id, action_type, requester, approver, status)


def log_task_completion(task_id: str, actor: str, iterations: int = 1,
                       duration_seconds: float = None):
    return get_audit_logger().log_task_completion(task_id, actor, iterations, duration_seconds)


def main():
    """Main entry point for testing and CLI usage"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Audit Logger CLI')
    parser.add_argument('--summary', action='store_true', help='Generate daily summary')
    parser.add_argument('--date', type=str, help='Date for logs (YYYY-MM-DD)')
    parser.add_argument('--actor', type=str, help='Filter by actor')
    parser.add_argument('--action-type', type=str, help='Filter by action type')
    parser.add_argument('--verify', action='store_true', help='Verify audit integrity')
    parser.add_argument('--test', action='store_true', help='Run test logging')
    
    args = parser.parse_args()
    
    vault_path = VAULT_PATH
    
    # Verify vault exists
    if not Path(vault_path).exists():
        print(f"Error: Vault path does not exist: {vault_path}")
        sys.exit(1)
    
    logger = AuditLogger(vault_path)
    
    try:
        if args.verify:
            # Verify audit integrity
            date = args.date or datetime.now().strftime('%Y-%m-%d')
            if logger.verify_audit_integrity(date):
                print(f"✅ Audit log integrity verified for {date}")
            else:
                print(f"❌ Audit log integrity check failed for {date}")
                sys.exit(1)
        
        elif args.summary:
            # Generate daily summary
            date = args.date or datetime.now().strftime('%Y-%m-%d')
            summary = logger.generate_daily_summary(date)
            print(json.dumps(summary, indent=2))
        
        elif args.actor:
            # Get logs by actor
            logs = logger.get_logs_by_actor(args.actor, args.date)
            print(json.dumps(logs, indent=2))
        
        elif args.action_type:
            # Get logs by action type
            logs = logger.get_logs_by_action_type(args.action_type, args.date)
            print(json.dumps(logs, indent=2))
        
        elif args.test:
            # Run test logging
            print("Running test audit logging...")
            
            logger.log_mcp_call('odoo-mcp', 'odoo_create_invoice',
                              {'partner_id': 1, 'amount': 1000})
            
            logger.log_file_operation('create', '/path/to/file.md', 'claude-code')
            
            logger.log_approval_request('APPROVAL_001', 'payment',
                                       'odoo-watcher', status='pending')
            
            logger.log_task_completion('TASK_001', 'ralph-loop', iterations=3)
            
            logger.log_email_action('send', 'test@example.com', 'Test Subject',
                                   'email-mcp')
            
            logger.log_social_media_action('facebook', 'post',
                                          'Test post content', 'facebook-mcp',
                                          'post_123')
            
            logger.log_accounting_action('invoice', 'out_invoice', 'INV/2026/001',
                                        1000.0, 'odoo-mcp')
            
            print("✅ Test audit logging completed")
            print(f"Logs written to: {logger.audit_file}")
        
        else:
            parser.print_help()
    
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
