#!/usr/bin/env python3
"""
Odoo MCP Helper - Start server and execute commands
Gold Tier Feature: Personal AI FTEs Project

Usage:
    python odoo.py auth                          # Authenticate with Odoo
    python odoo.py company                       # Get company info
    python odoo.py partners                      # List all partners
    python odoo.py customers                     # List customers only
    python odoo.py products                      # List all products
    python odoo.py invoices                      # List customer invoices
    python odoo.py bills                         # List vendor bills
    python odoo.py invoice 123                   # Get specific invoice
    python odoo.py summary                       # Get financial summary
    python odoo.py create-partner "Name"         # Create new partner
    python odoo.py create-product "Name" 100     # Create product with price
"""

import sys
import os
import subprocess
import json
from datetime import datetime

# Get the directory where this script is located
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
MCP_CLIENT = os.path.join(SCRIPT_DIR, 'mcp-client.py')
MCP_SERVER = os.path.join(SCRIPT_DIR, 'odoo_mcp_server.py')


def run_mcp_command(tool: str, params: dict):
    """Run an MCP command using the client"""
    # Load .env file to get credentials
    env_file = os.path.join(SCRIPT_DIR, '.env')

    # If .env doesn't exist in skill folder, try the scripts folder
    if not os.path.exists(env_file):
        env_file = os.path.join(os.path.dirname(SCRIPT_DIR), '..', 'AI_Employee_Vault', 'scripts', '.env')

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
        MCP_CLIENT,
        'call',
        '--stdio',
        f'python "{MCP_SERVER}"',
        '--tool',
        tool,
        '--params',
        json.dumps(params)
    ]

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30, env=env)
        if result.returncode == 0:
            return json.loads(result.stdout) if result.stdout.strip() else {}
        else:
            print(f"Error: {result.stderr}")
            return None
    except Exception as e:
        print(f"Error running command: {e}")
        return None


def format_currency(amount: float) -> str:
    """Format amount as currency"""
    if amount is None:
        return "$0.00"
    return f"${abs(amount):,.2f}"


def format_partner(partner: dict) -> str:
    """Format partner data for display"""
    name = partner.get('name', 'Unknown')
    email = partner.get('email', 'N/A')
    phone = partner.get('phone', 'N/A')
    customer = "✓" if partner.get('customer_rank', 0) > 0 else "✗"
    supplier = "✓" if partner.get('supplier_rank', 0) > 0 else "✗"
    return f"{name} | {email} | {phone} | Cust: {customer} | Sup: {supplier}"


def format_invoice(invoice: dict) -> str:
    """Format invoice data for display"""
    name = invoice.get('name', 'Unknown')
    partner = invoice.get('partner_id', ['Unknown', 'Unknown'])
    partner_name = partner[1] if isinstance(partner, list) else partner
    amount = invoice.get('amount_total', 0)
    residual = invoice.get('amount_residual', 0)
    state = invoice.get('state', 'draft')
    date = invoice.get('invoice_date', 'N/A')
    
    status_emoji = "✅" if state == 'posted' else "📝"
    paid_emoji = "✓" if residual == 0 else "✗"
    
    return f"{status_emoji} {name} | {partner_name} | {format_currency(amount)} | Due: {format_currency(residual)} | {date} | Paid: {paid_emoji}"


def authenticate():
    """Authenticate with Odoo"""
    print("🔐 Authenticating with Odoo...\n")
    
    # Load credentials from environment
    env_file = os.path.join(SCRIPT_DIR, '.env')
    username = 'admin'
    password = 'admin'
    
    if os.path.exists(env_file):
        with open(env_file, 'r') as f:
            for line in f:
                line = line.strip()
                if line.startswith('ODOO_USERNAME='):
                    username = line.split('=', 1)[1]
                elif line.startswith('ODOO_PASSWORD='):
                    password = line.split('=', 1)[1]
    
    result = run_mcp_command('odoo_authenticate', {
        'username': username,
        'password': password
    })
    
    # Parse result - MCP returns content array
    if result:
        content = result.get('content', [])
        if content:
            text = content[0].get('text', '')
            try:
                data = json.loads(text)
                if data.get('success'):
                    print(f"✅ Authentication successful!")
                    print(f"User ID: {data.get('uid')}")
                    return True
            except:
                pass
    
    print(f"❌ Authentication failed: {result}")
    return False


def _parse_mcp_result(result):
    """Parse MCP result to extract JSON data"""
    if not result:
        return None
    content = result.get('content', [])
    if content:
        text = content[0].get('text', '')
        try:
            return json.loads(text)
        except:
            return text
    return result


def get_company_info():
    """Get company information"""
    print("🏢 Company Information\n")
    print("=" * 60)
    result = run_mcp_command('odoo_get_company_info', {})
    data = _parse_mcp_result(result)
    
    if data:
        for key, value in data.items():
            if value:
                print(f"{key.replace('_', ' ').title()}: {value}")
    else:
        print("Failed to retrieve company information")


def get_partners(partner_type: str = 'all', limit: int = 20):
    """Get partners (customers/vendors)"""
    print(f"👥 Partners ({partner_type.title()})\n")
    print("=" * 80)

    result = run_mcp_command('odoo_get_partners', {
        'partner_type': partner_type,
        'limit': limit
    })
    data = _parse_mcp_result(result)

    if data and isinstance(data, list):
        print(f"{'Name':<30} | {'Email':<25} | {'Phone':<15} | {'Cust':<6} | {'Sup':<6}")
        print("-" * 80)
        for partner in data:
            name = partner.get('name', 'Unknown')[:28]
            email = partner.get('email', 'N/A')[:23]
            phone = partner.get('phone', 'N/A')[:13]
            customer = "✓" if partner.get('customer_rank', 0) > 0 else "✗"
            supplier = "✓" if partner.get('supplier_rank', 0) > 0 else "✗"
            print(f"{name:<30} | {email:<25} | {phone:<15} | {customer:<6} | {supplier:<6}")
        print(f"\nTotal: {len(data)} partners")
    else:
        print(f"Failed to retrieve partners or no partners found")


def get_products(limit: int = 20):
    """Get products"""
    print(f"📦 Products\n")
    print("=" * 80)

    result = run_mcp_command('odoo_get_products', {'limit': limit})
    data = _parse_mcp_result(result)

    if data and isinstance(data, list):
        print(f"{'Name':<35} | {'Code':<15} | {'Type':<10} | {'Price':<12} | {'Cost':<12}")
        print("-" * 80)
        for product in data:
            name = product.get('name', 'Unknown')[:33]
            code = product.get('default_code', 'N/A') or 'N/A'
            ptype = product.get('type', 'product')[:8]
            price = format_currency(product.get('list_price', 0))
            cost = format_currency(product.get('cost', 0))
            print(f"{name:<35} | {str(code):<15} | {ptype:<10} | {price:<12} | {cost:<12}")
        print(f"\nTotal: {len(data)} products")
    else:
        print("Failed to retrieve products or no products found")


def get_invoices(invoice_type: str = 'out_invoice', limit: int = 20):
    """Get invoices"""
    type_label = "Customer Invoices" if invoice_type == 'out_invoice' else "Vendor Bills"
    print(f"📄 {type_label}\n")
    print("=" * 100)

    result = run_mcp_command('odoo_get_invoices', {
        'invoice_type': invoice_type,
        'limit': limit
    })
    data = _parse_mcp_result(result)

    if data and isinstance(data, list):
        for invoice in data:
            print(format_invoice(invoice))
        print(f"\nTotal: {len(data)} invoices")
    else:
        print("Failed to retrieve invoices or no invoices found")


def get_invoice(invoice_id: int):
    """Get specific invoice details"""
    print(f"📄 Invoice #{invoice_id} Details\n")
    print("=" * 60)

    result = run_mcp_command('odoo_get_invoice', {'invoice_id': invoice_id})
    data = _parse_mcp_result(result)

    if data:
        for key, value in data.items():
            if key == 'partner_id' and isinstance(value, list):
                value = value[1]
            elif key == 'invoice_line_ids' and isinstance(value, list):
                print(f"\nInvoice Lines:")
                for line in value:
                    print(f"  - {line}")
                continue
            elif key in ['amount_total', 'amount_residual']:
                value = format_currency(value)
            print(f"{key.replace('_', ' ').title()}: {value}")
    else:
        print(f"Failed to retrieve invoice #{invoice_id}")


def get_financial_summary(month: int = None, year: int = None):
    """Get financial summary"""
    now = datetime.now()
    month = month or now.month
    year = year or now.year

    print(f"📊 Financial Summary - {year}-{month:02d}\n")
    print("=" * 60)

    result = run_mcp_command('odoo_get_financial_summary', {
        'month': month,
        'year': year
    })
    data = _parse_mcp_result(result)

    # Handle case where data is still a string
    if isinstance(data, str):
        try:
            data = json.loads(data)
        except:
            print(f"Raw result: {data}")
            return

    if data:
        print(f"Period: {data.get('period', 'N/A')}")
        print(f"\nRevenue & Expenses:")
        print(f"  Total Revenue:      {format_currency(data.get('total_revenue', 0))}")
        print(f"  Total Expenses:     {format_currency(data.get('total_expenses', 0))}")
        print(f"  Net Income:         {format_currency(data.get('total_revenue', 0) - data.get('total_expenses', 0))}")

        print(f"\nReceivables & Payables:")
        print(f"  Accounts Receivable: {format_currency(data.get('total_receivable', 0))}")
        print(f"  Accounts Payable:    {format_currency(data.get('total_payable', 0))}")

        print(f"\nInvoice Statistics:")
        print(f"  Customer Invoices:   {data.get('invoice_count', 0)}")
        print(f"  Vendor Bills:        {data.get('vendor_bill_count', 0)}")
    else:
        print("Failed to retrieve financial summary")


def create_partner(name: str, email: str = None, phone: str = None,
                   is_customer: bool = True, is_supplier: bool = False):
    """Create a new partner"""
    print(f"👥 Creating Partner: {name}\n")

    result = run_mcp_command('odoo_create_partner', {
        'name': name,
        'email': email,
        'phone': phone,
        'is_customer': is_customer,
        'is_supplier': is_supplier
    })
    data = _parse_mcp_result(result)

    # Handle string result
    if isinstance(data, str):
        try:
            data = json.loads(data)
        except:
            print(f"❌ Failed to create partner: {data}")
            return

    if data and data.get('success'):
        print(f"✅ Partner created successfully!")
        print(f"Partner ID: {data.get('partner_id')}")
    else:
        print(f"❌ Failed to create partner: {data}")


def create_product(name: str, price: float, cost: float = 0.0,
                   product_type: str = 'product'):
    """Create a new product"""
    print(f"📦 Creating Product: {name}\n")

    result = run_mcp_command('odoo_create_product', {
        'name': name,
        'list_price': price,
        'standard_price': cost,
        'product_type': product_type
    })
    data = _parse_mcp_result(result)

    # Handle string result
    if isinstance(data, str):
        try:
            data = json.loads(data)
        except:
            print(f"❌ Failed to create product: {data}")
            return

    if data and data.get('success'):
        print(f"✅ Product created successfully!")
        print(f"Product ID: {data.get('product_id')}")
        print(f"Name: {name}")
        print(f"Sale Price: {format_currency(price)}")
        print(f"Cost: {format_currency(cost)}")
        print(f"Type: {product_type}")
    else:
        print(f"❌ Failed to create product: {data}")


def create_invoice(partner_id: int, lines: list, date: str = None):
    """Create a new invoice"""
    print(f"📄 Creating Invoice\n")

    result = run_mcp_command('odoo_create_invoice', {
        'partner_id': partner_id,
        'invoice_lines': lines,
        'invoice_date': date
    })
    data = _parse_mcp_result(result)

    # Handle string result
    if isinstance(data, str):
        try:
            data = json.loads(data)
        except:
            print(f"❌ Failed to create invoice: {data}")
            return

    if data and data.get('success'):
        print(f"✅ Invoice created successfully!")
        print(f"Invoice ID: {data.get('invoice_id')}")
    else:
        print(f"❌ Failed to create invoice: {data}")


def validate_invoice(invoice_id: int):
    """Validate/post an invoice"""
    print(f"✓ Validating Invoice #{invoice_id}\n")

    result = run_mcp_command('odoo_validate_invoice', {'invoice_id': invoice_id})
    data = _parse_mcp_result(result)

    # Handle string result
    if isinstance(data, str):
        try:
            data = json.loads(data)
        except:
            print(f"❌ Failed to validate invoice: {data}")
            return

    if data and data.get('success'):
        print(f"✅ Invoice #{invoice_id} validated successfully!")
    else:
        print(f"❌ Failed to validate invoice: {data}")


def get_payments(limit: int = 20):
    """Get recent payments"""
    print(f"💰 Recent Payments\n")
    print("=" * 80)

    result = run_mcp_command('odoo_get_payments', {'limit': limit})
    data = _parse_mcp_result(result)

    if data and isinstance(data, list):
        print(f"{'ID':<10} | {'Partner':<25} | {'Date':<12} | {'Amount':<12} | {'Type':<10} | {'State':<10}")
        print("-" * 80)
        for payment in data:
            pid = payment.get('id', 'N/A')
            partner = payment.get('partner_id', ['N/A', 'N/A'])
            partner_name = partner[1] if isinstance(partner, list) else partner
            date = payment.get('date', 'N/A')
            amount = format_currency(payment.get('amount', 0))
            ptype = payment.get('payment_type', 'N/A')[:8]
            state = payment.get('state', 'N/A')
            print(f"{pid:<10} | {str(partner_name):<25} | {date:<12} | {amount:<12} | {ptype:<10} | {state:<10}")
        print(f"\nTotal: {len(data)} payments")
    else:
        print("Failed to retrieve payments or no payments found")


def show_help():
    """Show usage help"""
    print("""
Odoo MCP Helper - Gold Tier ERP Integration
============================================

Usage:
    python odoo.py <command> [arguments]

Authentication:
    auth                        Authenticate with Odoo

Company & Partners:
    company                     Get company information
    partners [type] [limit]     List partners (all/customer/supplier)
    customers [limit]           List customers only
    create-partner "Name"       Create new partner

Products:
    products [limit]            List products
    create-product "Name" price Create product with price

Invoices:
    invoices [limit]            List customer invoices
    bills [limit]               List vendor bills
    invoice <id>                Get specific invoice details
    create-invoice              Create new invoice (interactive)
    validate <id>               Validate/post invoice

Payments:
    payments [limit]            List recent payments

Financial Reports:
    summary [month] [year]      Get financial summary

Examples:
    python odoo.py auth
    python odoo.py company
    python odoo.py partners customer 10
    python odoo.py products 20
    python odoo.py invoices 15
    python odoo.py invoice 123
    python odoo.py summary 3 2026
    python odoo.py create-partner "Acme Corp" --email="info@acme.com"
    python odoo.py create-product "Consulting" 150 --type="service"
    python odoo.py validate 456

Notes:
    - Default limit is 20 for list commands
    - Partner types: all (default), customer, supplier
    - Invoice types: out_invoice (customer), in_invoice (vendor)
""")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        show_help()
        exit(0)

    command = sys.argv[1]

    if command == 'help':
        show_help()

    elif command == 'auth':
        authenticate()

    elif command == 'company':
        get_company_info()

    elif command == 'partners':
        partner_type = sys.argv[2] if len(sys.argv) > 2 else 'all'
        limit = int(sys.argv[3]) if len(sys.argv) > 3 else 20
        get_partners(partner_type, limit)

    elif command == 'customers':
        limit = int(sys.argv[2]) if len(sys.argv) > 2 else 20
        get_partners('customer', limit)

    elif command == 'products':
        limit = int(sys.argv[2]) if len(sys.argv) > 2 else 20
        get_products(limit)

    elif command == 'invoices':
        limit = int(sys.argv[2]) if len(sys.argv) > 2 else 20
        get_invoices('out_invoice', limit)

    elif command == 'bills':
        limit = int(sys.argv[2]) if len(sys.argv) > 2 else 20
        get_invoices('in_invoice', limit)

    elif command == 'invoice':
        if len(sys.argv) < 3:
            print("❌ Error: Invoice ID required")
            exit(1)
        invoice_id = int(sys.argv[2])
        get_invoice(invoice_id)

    elif command == 'summary':
        month = int(sys.argv[2]) if len(sys.argv) > 2 else None
        year = int(sys.argv[3]) if len(sys.argv) > 3 else None
        get_financial_summary(month, year)

    elif command == 'payments':
        limit = int(sys.argv[2]) if len(sys.argv) > 2 else 20
        get_payments(limit)

    elif command == 'create-partner':
        if len(sys.argv) < 3:
            print("❌ Error: Partner name required")
            exit(1)
        name = sys.argv[2]
        # Parse optional arguments
        email = None
        phone = None
        is_customer = True
        is_supplier = False
        
        for i, arg in enumerate(sys.argv[3:], 3):
            if arg.startswith('--email='):
                email = arg.split('=', 1)[1]
            elif arg.startswith('--phone='):
                phone = arg.split('=', 1)[1]
            elif arg == '--supplier':
                is_supplier = True
        
        create_partner(name, email, phone, is_customer, is_supplier)

    elif command == 'create-product':
        if len(sys.argv) < 4:
            print("❌ Error: Product name and price required")
            exit(1)
        name = sys.argv[2]
        try:
            price = float(sys.argv[3])
        except ValueError:
            print("❌ Error: Price must be a number")
            exit(1)
        
        cost = 0.0
        product_type = 'product'
        
        for arg in sys.argv[4:]:
            if arg.startswith('--cost='):
                cost = float(arg.split('=', 1)[1])
            elif arg.startswith('--type='):
                product_type = arg.split('=', 1)[1]
        
        create_product(name, price, cost, product_type)

    elif command == 'validate':
        if len(sys.argv) < 3:
            print("❌ Error: Invoice ID required")
            exit(1)
        invoice_id = int(sys.argv[2])
        validate_invoice(invoice_id)

    elif command == 'create-invoice':
        print("Interactive invoice creation not yet implemented.")
        print("Use Claude Code with @odoo odoo_create_invoice instead.")

    else:
        print(f"❌ Unknown command: {command}")
        show_help()
        exit(1)
