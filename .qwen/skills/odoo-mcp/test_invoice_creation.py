#!/usr/bin/env python3
"""
Test Invoice Creation via Odoo MCP
Demonstrates how Qwen Code (the brain) creates invoices automatically
"""

import subprocess
import json
import sys
import os

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
MCP_CLIENT = os.path.join(SCRIPT_DIR, 'mcp-client.py')
MCP_SERVER = os.path.join(SCRIPT_DIR, 'odoo_mcp_server.py')

def run_mcp(tool, params):
    """Run MCP command"""
    env = os.environ.copy()
    env['ODOO_URL'] = 'http://localhost:8069'
    env['ODOO_DB'] = 'odoo'
    env['ODOO_USERNAME'] = 'admin'
    env['ODOO_PASSWORD'] = 'admin'
    
    cmd = [
        sys.executable, MCP_CLIENT, 'call',
        '--stdio', f'python "{MCP_SERVER}"',
        '--tool', tool,
        '--params', json.dumps(params)
    ]
    
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=30, env=env)
    if result.returncode == 0:
        output = json.loads(result.stdout)
        content = output.get('content', [{}])[0].get('text', '')
        try:
            return json.loads(content)
        except:
            return content
    return None

print("=" * 60)
print("DEMO: Qwen Code Creating Invoice Automatically")
print("=" * 60)

# Step 1: Authenticate
print("\n1️⃣  Authenticating with Odoo...")
auth = run_mcp('odoo_authenticate', {'username': 'admin', 'password': 'admin'})
if auth and auth.get('success'):
    print(f"   ✅ Authenticated (User ID: {auth['uid']})")
else:
    print("   ❌ Authentication failed")
    sys.exit(1)

# Step 2: Get partner
print("\n2️⃣  Finding customer: Acme Corporation...")
partners = run_mcp('odoo_get_partners', {'partner_type': 'all', 'limit': 50})
acme_id = None
if partners and isinstance(partners, list):
    for p in partners:
        if p.get('name') == 'Acme Corporation':
            acme_id = p['id']
            print(f"   ✅ Found Acme Corporation (ID: {acme_id})")
            break

if not acme_id:
    print("   ❌ Acme Corporation not found")
    sys.exit(1)

# Step 3: Create invoice
print("\n3️⃣  Creating invoice...")
print("   📝 Details:")
print("      - Customer: Acme Corporation")
print("      - Service: Web Development")
print("      - Quantity: 10 hours")
print("      - Rate: $200/hour")
print("      - Total: $2,000")

invoice = run_mcp('odoo_create_invoice', {
    'partner_id': acme_id,
    'invoice_lines': [{
        'name': 'Web Development Service',
        'quantity': 10,
        'price_unit': 200
    }]
})

if invoice and isinstance(invoice, dict) and invoice.get('success'):
    print(f"\n   ✅ Invoice created successfully!")
    print(f"   📄 Invoice ID: {invoice.get('invoice_id')}")
    print(f"   🔗 View in Odoo: http://localhost:8069/web#model=account.move&id={invoice.get('invoice_id')}")
else:
    print(f"\n   ❌ Invoice creation failed: {invoice}")

print("\n" + "=" * 60)
print("DEMO COMPLETE")
print("=" * 60)
