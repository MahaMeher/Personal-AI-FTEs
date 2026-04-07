#!/usr/bin/env python3
"""
Odoo Watcher - Monitors Odoo ERP for accounting events and creates action files

Gold Tier Feature: Personal AI FTEs Project
Monitors Odoo for:
- Overdue invoices (older than due date)
- Unpaid vendor bills requiring approval
- Low bank balance alerts
- Large transactions requiring review
- Monthly financial summary triggers
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

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('odoo_watcher.log')
    ]
)
logger = logging.getLogger('odoo-watcher')

# Configuration
ODOO_URL = os.getenv('ODOO_URL', 'http://localhost:8069')
ODOO_DB = os.getenv('ODOO_DB', 'postgres')
ODOO_USERNAME = os.getenv('ODOO_USERNAME', 'admin')
ODOO_PASSWORD = os.getenv('ODOO_PASSWORD', 'admin')
VAULT_PATH = os.getenv('VAULT_PATH', 'D:/Personal-AI-FTEs/AI_Employee_Vault')
CHECK_INTERVAL = int(os.getenv('CHECK_INTERVAL', '300'))  # 5 minutes

# Thresholds
OVERDUE_DAYS_THRESHOLD = 7  # Flag invoices overdue by more than 7 days
LOW_BALANCE_THRESHOLD = 1000.0  # Alert if bank balance below this
LARGE_TRANSACTION_THRESHOLD = 5000.0  # Flag transactions above this amount
PAYMENT_APPROVAL_THRESHOLD = 1000.0  # Require approval for payments above this


class OdooClient:
    """Simple Odoo JSON-RPC client for Watcher"""
    
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
                logger.info(f"Authenticated with Odoo (UID: {self.uid})")
                return True
            else:
                logger.error("Odoo authentication failed")
                return False
                
        except Exception as e:
            logger.error(f"Authentication error: {e}")
            return False
    
    def execute_kw(self, model: str, method: str, args: list = None, kwargs: dict = None) -> Any:
        """Execute Odoo ORM method"""
        if not self.uid:
            if not self.authenticate():
                raise Exception("Not authenticated with Odoo")
        
        try:
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
                error_msg = result['error'].get('data', {}).get('message', 'Unknown error')
                raise Exception(f"Odoo error: {error_msg}")
            
            return result.get('result')
            
        except Exception as e:
            logger.error(f"Execute error: {e}")
            raise
    
    def search_read(self, model: str, domain: list = None, fields: list = None, limit: int = 80) -> list:
        """Search and read records"""
        return self.execute_kw(
            model, 
            'search_read', 
            [domain or []], 
            {'fields': fields, 'limit': limit}
        )


class OdooWatcher:
    """Monitor Odoo ERP for accounting events"""
    
    def __init__(self, vault_path: str, check_interval: int = 300):
        self.vault_path = Path(vault_path)
        self.needs_action = self.vault_path / 'Needs_Action'
        self.accounting_folder = self.vault_path / 'Accounting'
        self.check_interval = check_interval
        self.processed_items = set()
        
        # Initialize Odoo client
        self.odoo_client = OdooClient(ODOO_URL, ODOO_DB, ODOO_USERNAME, ODOO_PASSWORD)
        
        # Ensure directories exist
        self.needs_action.mkdir(parents=True, exist_ok=True)
        self.accounting_folder.mkdir(parents=True, exist_ok=True)
        
        # Load previously processed items
        self._load_processed_items()
        
    def _load_processed_items(self):
        """Load processed item IDs from cache"""
        cache_file = self.vault_path / '.odoo_processed.json'
        if cache_file.exists():
            try:
                with open(cache_file, 'r') as f:
                    self.processed_items = set(json.load(f))
                logger.info(f"Loaded {len(self.processed_items)} processed items from cache")
            except Exception as e:
                logger.error(f"Error loading cache: {e}")
                self.processed_items = set()
    
    def _save_processed_items(self):
        """Save processed item IDs to cache"""
        cache_file = self.vault_path / '.odoo_processed.json'
        try:
            items_to_save = list(self.processed_items)[-1000:]
            with open(cache_file, 'w') as f:
                json.dump(items_to_save, f)
        except Exception as e:
            logger.error(f"Error saving cache: {e}")
    
    def _generate_item_id(self, item: dict) -> str:
        """Generate unique ID for an item"""
        content = f"{item.get('id', '')}{item.get('write_date', datetime.now().isoformat())}"
        return hashlib.md5(content.encode()).hexdigest()[:16]
    
    def check_for_updates(self) -> list:
        """Check for accounting events in Odoo"""
        new_items = []
        
        # Ensure authenticated
        if not self.odoo_client.uid:
            if not self.odoo_client.authenticate():
                logger.error("Failed to authenticate with Odoo")
                return []
        
        # Check for overdue invoices
        try:
            overdue = self._get_overdue_invoices()
            for invoice in overdue:
                item_id = self._generate_item_id(invoice)
                if item_id not in self.processed_items:
                    invoice['alert_type'] = 'overdue_invoice'
                    new_items.append(invoice)
                    self.processed_items.add(item_id)
        except Exception as e:
            logger.error(f"Error checking overdue invoices: {e}")
        
        # Check for unpaid vendor bills
        try:
            unpaid_bills = self._get_unpaid_vendor_bills()
            for bill in unpaid_bills:
                item_id = self._generate_item_id(bill)
                if item_id not in self.processed_items:
                    bill['alert_type'] = 'unpaid_vendor_bill'
                    new_items.append(bill)
                    self.processed_items.add(item_id)
        except Exception as e:
            logger.error(f"Error checking unpaid bills: {e}")
        
        # Check for large transactions
        try:
            large_txns = self._get_large_transactions()
            for txn in large_txns:
                item_id = self._generate_item_id(txn)
                if item_id not in self.processed_items:
                    txn['alert_type'] = 'large_transaction'
                    new_items.append(txn)
                    self.processed_items.add(item_id)
        except Exception as e:
            logger.error(f"Error checking large transactions: {e}")
        
        # Check for low bank balance
        try:
            low_balance = self._check_bank_balance()
            if low_balance:
                item_id = self._generate_item_id(low_balance)
                if item_id not in self.processed_items:
                    low_balance['alert_type'] = 'low_bank_balance'
                    new_items.append(low_balance)
                    self.processed_items.add(item_id)
        except Exception as e:
            logger.error(f"Error checking bank balance: {e}")
        
        # Check for invoices awaiting approval
        try:
            awaiting_approval = self._get_draft_invoices()
            for invoice in awaiting_approval:
                item_id = self._generate_item_id(invoice)
                if item_id not in self.processed_items:
                    invoice['alert_type'] = 'invoice_approval_required'
                    new_items.append(invoice)
                    self.processed_items.add(item_id)
        except Exception as e:
            logger.error(f"Error checking draft invoices: {e}")
        
        # Save cache
        self._save_processed_items()
        
        return new_items
    
    def _get_overdue_invoices(self, limit: int = 50) -> list:
        """Get customer invoices that are overdue"""
        today = datetime.now().strftime('%Y-%m-%d')
        overdue_date = (datetime.now() - timedelta(days=OVERDUE_DAYS_THRESHOLD)).strftime('%Y-%m-%d')
        
        domain = [
            ('move_type', '=', 'out_invoice'),
            ('state', '=', 'posted'),
            ('payment_state', 'in', ['not_paid', 'partial']),
            ('invoice_date_due', '<', today),
            ('invoice_date_due', '<', overdue_date)
        ]
        
        fields = ['id', 'name', 'partner_id', 'invoice_date', 'invoice_date_due',
                  'amount_total', 'amount_residual', 'state', 'payment_state']
        
        return self.odoo_client.search_read('account.move', domain, fields, limit)
    
    def _get_unpaid_vendor_bills(self, limit: int = 50) -> list:
        """Get vendor bills that are unpaid or partially paid"""
        domain = [
            ('move_type', 'in', ['in_invoice', 'in_refund']),
            ('state', '=', 'posted'),
            ('payment_state', 'in', ['not_paid', 'partial'])
        ]
        
        fields = ['id', 'name', 'partner_id', 'invoice_date', 'invoice_date_due',
                  'amount_total', 'amount_residual', 'state', 'payment_state']
        
        return self.odoo_client.search_read('account.move', domain, fields, limit)
    
    def _get_large_transactions(self, limit: int = 20) -> list:
        """Get large accounting entries"""
        domain = [
            ('balance', '>', LARGE_TRANSACTION_THRESHOLD),
            ('parent_state', '=', 'posted')
        ]
        
        fields = ['id', 'name', 'date', 'account_id', 'debit', 'credit', 
                  'balance', 'partner_id', 'state', 'move_id']
        
        return self.odoo_client.search_read('account.move.line', domain, fields, limit)
    
    def _check_bank_balance(self) -> Optional[dict]:
        """Check if bank balance is below threshold"""
        # Get cash and bank accounts
        domain = [
            ('account_type', 'in', ['asset_cash', 'asset_current']),
            ('internal_type', '=', 'liquidity')
        ]
        
        fields = ['id', 'code', 'name', 'balance']
        accounts = self.odoo_client.search_read('account.account', domain, fields)
        
        alerts = []
        for account in accounts:
            balance = account.get('balance', 0)
            if abs(balance) < LOW_BALANCE_THRESHOLD:
                alerts.append({
                    'account_id': account['id'],
                    'account_code': account['code'],
                    'account_name': account['name'],
                    'balance': balance,
                    'threshold': LOW_BALANCE_THRESHOLD
                })
        
        # Return most critical alert
        if alerts:
            return min(alerts, key=lambda x: abs(x['balance']))
        return None
    
    def _get_draft_invoices(self, limit: int = 20) -> list:
        """Get draft invoices awaiting approval"""
        domain = [
            ('move_type', '=', 'out_invoice'),
            ('state', '=', 'draft')
        ]
        
        fields = ['id', 'name', 'partner_id', 'invoice_date', 'amount_total', 
                  'state', 'create_uid', 'create_date']
        
        return self.odoo_client.search_read('account.move', domain, fields, limit)
    
    def create_action_file(self, item: dict) -> Optional[Path]:
        """Create .md action file in Needs_Action folder"""
        alert_type = item.get('alert_type', 'unknown')
        item_id = item.get('id', 'unknown')
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        # Determine priority based on alert type
        if alert_type == 'overdue_invoice':
            prefix = 'ODOO_OVERDUE'
            priority = 'high'
        elif alert_type == 'low_bank_balance':
            prefix = 'ODOO_LOW_BALANCE'
            priority = 'critical'
        elif alert_type == 'large_transaction':
            prefix = 'ODOO_LARGE_TXN'
            priority = 'high'
        elif alert_type == 'unpaid_vendor_bill':
            prefix = 'ODOO_VENDOR_BILL'
            priority = 'normal'
        elif alert_type == 'invoice_approval_required':
            prefix = 'ODOO_APPROVAL'
            priority = 'normal'
        else:
            prefix = 'ODOO_ALERT'
            priority = 'normal'
        
        filename = f"{prefix}_{timestamp}_{item_id}.md"
        filepath = self.needs_action / filename
        
        # Generate content based on alert type
        if alert_type == 'overdue_invoice':
            content = self._create_overdue_invoice_content(item)
        elif alert_type == 'unpaid_vendor_bill':
            content = self._create_vendor_bill_content(item)
        elif alert_type == 'large_transaction':
            content = self._create_large_transaction_content(item)
        elif alert_type == 'low_bank_balance':
            content = self._create_low_balance_content(item)
        elif alert_type == 'invoice_approval_required':
            content = self._create_approval_content(item)
        else:
            content = self._create_generic_content(item)
        
        try:
            filepath.write_text(content, encoding='utf-8')
            logger.info(f"Created action file: {filepath.name}")
            return filepath
        except Exception as e:
            logger.error(f"Error creating action file: {e}")
            return None
    
    def _create_overdue_invoice_content(self, item: dict) -> str:
        """Create content for overdue invoice alert"""
        partner = item.get('partner_id', ['Unknown', 'Unknown'])[1] if isinstance(item.get('partner_id'), list) else 'Unknown'
        amount = item.get('amount_residual', item.get('amount_total', 0))
        due_date = item.get('invoice_date_due', 'Unknown')
        invoice_name = item.get('name', 'Unknown')
        days_overdue = (datetime.now() - datetime.strptime(due_date, '%Y-%m-%d')).days if due_date != 'Unknown' else 0
        
        return f"""---
type: odoo_alert
alert_type: overdue_invoice
invoice_id: {item.get('id')}
invoice_name: {invoice_name}
customer: {partner}
amount_total: {item.get('amount_total', 0)}
amount_due: {amount}
due_date: {due_date}
days_overdue: {days_overdue}
priority: high
created: {datetime.now().isoformat()}
status: pending
---

# Overdue Invoice Alert 🚨

## Invoice Details

- **Invoice:** {invoice_name}
- **Customer:** {partner}
- **Original Amount:** ${item.get('amount_total', 0):,.2f}
- **Amount Due:** ${amount:,.2f}
- **Due Date:** {due_date}
- **Days Overdue:** {days_overdue} days

## Situation

This invoice is **{days_overdue} days overdue** and remains unpaid. The customer has been sent {days_overdue // 7} reminder(s).

## Suggested Actions

- [ ] Send payment reminder email to customer
- [ ] Call customer to discuss payment status
- [ ] Check if there's a dispute or issue
- [ ] Consider payment plan if customer is facing difficulties
- [ ] Escalate to collections if > 60 days overdue
- [ ] Update Odoo with communication log

## Draft Reminder Email

```
Subject: Payment Reminder - Invoice {invoice_name}

Dear {partner.split()[0] if partner else 'Valued Customer'},

We hope this message finds you well.

This is a friendly reminder that invoice {invoice_name} for ${amount:,.2f} 
was due on {due_date} and is now {days_overdue} days overdue.

If you've already sent the payment, please disregard this notice. 
Otherwise, we would appreciate your prompt attention to this matter.

Please let us know if you have any questions or concerns about this invoice.

Best regards,
Accounts Receivable Team
```

## Odoo Actions

1. Open invoice in Odoo: {ODOO_URL}/web#action=account_move&action_id=account_move
2. Send reminder from invoice view
3. Log all communication in chatter

---
*Generated by Odoo Watcher - Gold Tier Feature*
"""
    
    def _create_vendor_bill_content(self, item: dict) -> str:
        """Create content for unpaid vendor bill"""
        partner = item.get('partner_id', ['Unknown', 'Unknown'])[1] if isinstance(item.get('partner_id'), list) else 'Unknown'
        amount = item.get('amount_residual', item.get('amount_total', 0))
        due_date = item.get('invoice_date_due', 'Unknown')
        bill_name = item.get('name', 'Unknown')
        
        return f"""---
type: odoo_alert
alert_type: unpaid_vendor_bill
bill_id: {item.get('id')}
bill_name: {bill_name}
vendor: {partner}
amount_total: {item.get('amount_total', 0)}
amount_due: {amount}
due_date: {due_date}
priority: normal
created: {datetime.now().isoformat()}
status: pending_approval
---

# Unpaid Vendor Bill - Payment Approval Required

## Bill Details

- **Bill:** {bill_name}
- **Vendor:** {partner}
- **Total Amount:** ${item.get('amount_total', 0):,.2f}
- **Amount Due:** ${amount:,.2f}
- **Due Date:** {due_date}

## Situation

This vendor bill is recorded in Odoo and awaiting payment processing.

## Suggested Actions

- [ ] Verify goods/services were received
- [ ] Match bill with purchase order (if applicable)
- [ ] Confirm payment terms
- [ ] Schedule payment before due date
- [ ] Process payment through Odoo
- [ ] File payment confirmation

## Payment Details

- **Payment Method:** [ ] Bank Transfer [ ] Check [ ] Credit Card
- **Journal:** [Select appropriate journal]
- **Payment Date:** [Schedule date]

## Approval

**Requires human approval for payment processing.**

Move this file to `/Approved` to proceed with payment.

---
*Generated by Odoo Watcher - Gold Tier Feature*
"""
    
    def _create_large_transaction_content(self, item: dict) -> str:
        """Create content for large transaction alert"""
        partner = item.get('partner_id', ['Unknown', 'Unknown'])[1] if isinstance(item.get('partner_id'), list) else 'Unknown'
        amount = abs(item.get('balance', 0))
        account = item.get('account_id', ['Unknown', 'Unknown'])[1] if isinstance(item.get('account_id'), list) else 'Unknown'
        
        return f"""---
type: odoo_alert
alert_type: large_transaction
transaction_id: {item.get('id')}
amount: {amount}
account: {account}
partner: {partner}
date: {item.get('date', 'Unknown')}
priority: high
created: {datetime.now().isoformat()}
status: pending_review
---

# Large Transaction Alert - Review Required

## Transaction Details

- **Transaction ID:** {item.get('id')}
- **Date:** {item.get('date', 'Unknown')}
- **Amount:** ${amount:,.2f}
- **Account:** {account}
- **Partner:** {partner}
- **Description:** {item.get('name', 'N/A')}

## Situation

This transaction exceeds the threshold of ${LARGE_TRANSACTION_THRESHOLD:,.2f} and requires human review.

## Review Checklist

- [ ] Verify transaction is legitimate
- [ ] Confirm proper authorization was obtained
- [ ] Check supporting documentation
- [ ] Ensure correct account coding
- [ ] Verify tax treatment
- [ ] Log review in Odoo chatter

## Red Flags to Check

- [ ] Unknown or unexpected vendor
- [ ] Round dollar amount (potential fraud indicator)
- [ ] Transaction outside normal business operations
- [ ] Missing or incomplete documentation
- [ ] Duplicate payment

## Action Required

**This transaction requires human review before proceeding.**

Please review and either:
1. Approve - Move to `/Approved`
2. Flag for Investigation - Move to `/Rejected` with notes

---
*Generated by Odoo Watcher - Gold Tier Feature*
"""
    
    def _create_low_balance_content(self, item: dict) -> str:
        """Create content for low bank balance alert"""
        balance = item.get('balance', 0)
        account_name = item.get('account_name', 'Unknown')
        account_code = item.get('account_code', 'Unknown')
        
        return f"""---
type: odoo_alert
alert_type: low_bank_balance
account_id: {item.get('account_id')}
account_name: {account_name}
account_code: {account_code}
current_balance: {balance}
threshold: {LOW_BALANCE_THRESHOLD}
priority: critical
created: {datetime.now().isoformat()}
status: pending_action
---

# Low Bank Balance Alert - Immediate Action Required 🚨

## Account Details

- **Account:** {account_name} ({account_code})
- **Current Balance:** ${balance:,.2f}
- **Alert Threshold:** ${LOW_BALANCE_THRESHOLD:,.2f}
- **Shortfall:** ${LOW_BALANCE_THRESHOLD - balance:,.2f}

## Situation

This account balance has fallen below the minimum threshold. Immediate action is required to avoid:
- Bounced payments
- Overdraft fees
- Vendor payment issues
- Cash flow problems

## Immediate Actions Required

- [ ] Review upcoming scheduled payments
- [ ] Identify incoming receivables
- [ ] Consider delaying non-essential payments
- [ ] Arrange short-term financing if needed
- [ ] Transfer funds from reserve account
- [ ] Update cash flow forecast

## Cash Flow Analysis

### Upcoming Payments (Next 7 Days)
[Review Odoo for scheduled payments]

### Expected Receivables (Next 7 Days)
[Review Odoo for customer payments due]

## Recommendations

1. **Immediate:** Transfer funds to cover shortfall
2. **Short-term:** Accelerate collections on overdue invoices
3. **Medium-term:** Review and update cash flow forecasting
4. **Long-term:** Establish line of credit for emergencies

## Escalation

**This is a CRITICAL alert requiring immediate human attention.**

Contact:
- CFO/Finance Manager
- Business Owner
- Banking Relationship Manager

---
*Generated by Odoo Watcher - Gold Tier Feature*
"""
    
    def _create_approval_content(self, item: dict) -> str:
        """Create content for invoice approval request"""
        partner = item.get('partner_id', ['Unknown', 'Unknown'])[1] if isinstance(item.get('partner_id'), list) else 'Unknown'
        amount = item.get('amount_total', 0)
        invoice_name = item.get('name', 'Unknown')
        created_by = item.get('create_uid', ['Unknown', 'Unknown'])[1] if isinstance(item.get('create_uid'), list) else 'Unknown'
        
        return f"""---
type: odoo_alert
alert_type: invoice_approval_required
invoice_id: {item.get('id')}
invoice_name: {invoice_name}
customer: {partner}
amount: {amount}
created_by: {created_by}
priority: normal
created: {datetime.now().isoformat()}
status: pending_approval
---

# Invoice Approval Required

## Invoice Details

- **Invoice:** {invoice_name}
- **Customer:** {partner}
- **Amount:** ${amount:,.2f}
- **Created By:** {created_by}
- **Created Date:** {item.get('create_date', 'Unknown')}

## Situation

This invoice is in draft status and requires approval before posting.

## Approval Checklist

- [ ] Verify products/services were delivered
- [ ] Confirm pricing is correct
- [ ] Check customer credit limit
- [ ] Validate tax calculations
- [ ] Ensure proper account coding

## Action Required

**Move this file to `/Approved` to post the invoice.**

Or move to `/Rejected` if changes are needed.

---
*Generated by Odoo Watcher - Gold Tier Feature*
"""
    
    def _create_generic_content(self, item: dict) -> str:
        """Create generic alert content"""
        return f"""---
type: odoo_alert
alert_type: {item.get('alert_type', 'unknown')}
priority: normal
created: {datetime.now().isoformat()}
status: pending
---

# Odoo Alert

## Details

{json.dumps(item, indent=2, default=str)}

## Action Required

Please review this alert and take appropriate action.

---
*Generated by Odoo Watcher - Gold Tier Feature*
"""
    
    def run(self):
        """Main watcher loop"""
        logger.info(f"Starting Odoo Watcher (checking every {self.check_interval}s)")
        logger.info(f"Monitoring Odoo at: {ODOO_URL}")
        
        while True:
            try:
                items = self.check_for_updates()
                
                if items:
                    logger.info(f"Found {len(items)} new accounting events")
                    for item in items:
                        filepath = self.create_action_file(item)
                        if filepath:
                            logger.info(f"Created action file: {filepath.name}")
                else:
                    logger.debug("No new accounting events")
                
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
    
    # Verify Odoo credentials
    if not ODOO_URL or not ODOO_USERNAME or not ODOO_PASSWORD:
        logger.error("Missing Odoo credentials. Set ODOO_URL, ODOO_USERNAME, ODOO_PASSWORD")
        sys.exit(1)
    
    # Create and run watcher
    watcher = OdooWatcher(vault_path, CHECK_INTERVAL)
    
    try:
        watcher.run()
    except KeyboardInterrupt:
        logger.info("Odoo Watcher stopped by user")
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
