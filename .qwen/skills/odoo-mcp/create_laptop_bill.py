#!/usr/bin/env python3
"""
Create vendor bill for laptop purchase - 70,000 Rs. for Acme Corporation
"""

import requests
import json
from datetime import datetime

# Odoo configuration
ODOO_URL = "http://localhost:8069"
ODOO_DB = "odoo"
ODOO_USERNAME = "admin"
ODOO_PASSWORD = "admin"

class OdooClient:
    def __init__(self, url, db, username, password):
        self.url = url.rstrip('/')
        self.db = db
        self.username = username
        self.password = password
        self.uid = None
        self.session = requests.Session()
        
    def authenticate(self):
        """Authenticate with Odoo"""
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
            print(f"✅ Authenticated successfully (UID: {self.uid})")
            return True
        return False
    
    def execute_kw(self, model, method, args=None, kwargs=None):
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
    
    def create_vendor(self, name, email=None, phone=None):
        """Create a vendor (supplier)"""
        values = {
            'name': name,
            'email': email,
            'phone': phone,
            'customer_rank': 0,
            'supplier_rank': 1
        }
        
        vendor_id = self.execute_kw('res.partner', 'create', [[values]])
        print(f"✅ Created vendor: {name} (ID: {vendor_id})")
        return vendor_id
    
    def find_vendor(self, name):
        """Find vendor by name"""
        domain = [('name', '=', name), ('supplier_rank', '>', 0)]
        result = self.execute_kw('res.partner', 'search_read', [domain], {'fields': ['id', 'name'], 'limit': 1})
        
        if result and len(result) > 0:
            print(f"✅ Found vendor: {result[0]['name']} (ID: {result[0]['id']})")
            return result[0]['id']
        return None
    
    def create_vendor_bill(self, partner_id, invoice_lines, invoice_date=None):
        """Create a vendor bill (in_invoice)"""
        # Convert invoice lines to Odoo format
        odoo_lines = []
        for line in invoice_lines:
            odoo_lines.append((0, 0, {
                'name': line.get('name', 'Item'),
                'quantity': line.get('quantity', 1),
                'price_unit': line.get('price_unit', 0)
            }))
        
        values = {
            'move_type': 'in_invoice',  # Vendor bill
            'partner_id': partner_id,
            'invoice_date': invoice_date or datetime.now().strftime('%Y-%m-%d'),
            'invoice_line_ids': odoo_lines,
        }
        
        bill_id = self.execute_kw('account.move', 'create', [[values]])
        print(f"✅ Created vendor bill (ID: {bill_id})")
        return bill_id
    
    def validate_bill(self, bill_id):
        """Post/validate the vendor bill"""
        result = self.execute_kw('account.move', 'action_post', [[bill_id]])
        print(f"✅ Validated/posted vendor bill (ID: {bill_id})")
        return result

def main():
    # Initialize Odoo client
    client = OdooClient(ODOO_URL, ODOO_DB, ODOO_USERNAME, ODOO_PASSWORD)
    
    # Authenticate
    if not client.authenticate():
        print("❌ Authentication failed!")
        return
    
    # Step 1: Find or create Acme Corporation vendor
    vendor_name = "Acme Corporation"
    vendor_id = client.find_vendor(vendor_name)
    
    if not vendor_id:
        print(f"\n📝 Creating new vendor: {vendor_name}")
        vendor_id = client.create_vendor(
            name=vendor_name,
            email="billing@acmecorp.com",
            phone="+91 1234567890"
        )
        # Extract integer from list if needed
        if isinstance(vendor_id, list):
            vendor_id = vendor_id[0]
    
    # Ensure vendor_id is an integer
    if isinstance(vendor_id, list):
        vendor_id = vendor_id[0]
    
    # Step 2: Create vendor bill for laptop purchase
    print(f"\n💰 Creating vendor bill for laptop purchase...")
    
    invoice_lines = [
        {
            'name': 'Laptop - High Performance (70,000 Rs.)',
            'quantity': 1,
            'price_unit': 70000
        }
    ]
    
    bill_id = client.create_vendor_bill(
        partner_id=vendor_id,
        invoice_lines=invoice_lines,
        invoice_date=datetime.now().strftime('%Y-%m-%d')
    )
    
    # Extract integer from list if needed
    if isinstance(bill_id, list):
        bill_id = bill_id[0]
    
    # Step 3: Get bill details to confirm
    print(f"\n📋 Retrieving bill details...")
    bill_data = client.execute_kw('account.move', 'read', [[bill_id]], {'fields': ['name', 'partner_id', 'amount_total', 'state', 'move_type']})
    
    if bill_data:
        bill = bill_data[0]
        print(f"\n{'='*60}")
        print(f"📄 VENDOR BILL CREATED")
        print(f"{'='*60}")
        print(f"Bill Number: {bill.get('name', 'Draft')}")
        print(f"Vendor: {bill.get('partner_id', [None, vendor_name])[1] if isinstance(bill.get('partner_id'), list) else vendor_name}")
        print(f"Amount: Rs. {bill.get('amount_total', 70000):,.2f}")
        print(f"State: {bill.get('state', 'draft')}")
        print(f"Type: {bill.get('move_type', 'in_invoice')}")
        print(f"Date: {datetime.now().strftime('%Y-%m-%d')}")
        print(f"{'='*60}")
        print(f"\n✅ Vendor bill created successfully in Draft state!")
        print(f"   You can view it at: {ODOO_URL}/web#model=account.move&view_type=form&id={bill_id}")
    
    # Optional: Validate/post the bill (uncomment if you want to post immediately)
    print(f"\n📤 Posting vendor bill...")
    client.validate_bill(bill_id)
    
    # Get updated bill details
    bill_data = client.execute_kw('account.move', 'read', [[bill_id]], {'fields': ['name', 'partner_id', 'amount_total', 'state', 'move_type']})
    if bill_data:
        bill = bill_data[0]
        print(f"\n{'='*60}")
        print(f"📄 VENDOR BILL POSTED")
        print(f"{'='*60}")
        print(f"Bill Number: {bill.get('name', 'N/A')}")
        print(f"Vendor: {bill.get('partner_id', [None, vendor_name])[1] if isinstance(bill.get('partner_id'), list) else vendor_name}")
        print(f"Amount: Rs. {bill.get('amount_total', 70000):,.2f}")
        print(f"State: {bill.get('state', 'posted')}")
        print(f"Type: {bill.get('move_type', 'in_invoice')}")
        print(f"Date: {datetime.now().strftime('%Y-%m-%d')}")
        print(f"{'='*60}")
        print(f"\n✅ Vendor bill posted successfully!")
        print(f"   You can view it at: {ODOO_URL}/web#model=account.move&view_type=form&id={bill_id}")

if __name__ == "__main__":
    main()
