#!/usr/bin/env python3
"""
Odoo MCP Server - Model Context Protocol Server for Odoo ERP Integration

This MCP server provides tools for interacting with Odoo Community Edition
via JSON-RPC API for accounting, invoicing, and business operations.

Gold Tier Feature: Personal AI FTEs Project
"""

import asyncio
import json
import logging
import os
from typing import Any, Optional
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
logger = logging.getLogger('odoo-mcp')

# Environment variables
ODOO_URL = os.getenv('ODOO_URL', 'http://localhost:8069')
ODOO_DB = os.getenv('ODOO_DB', 'postgres')
ODOO_USERNAME = os.getenv('ODOO_USERNAME', 'admin')
ODOO_PASSWORD = os.getenv('ODOO_PASSWORD', 'admin')

class OdooClient:
    """Client for Odoo JSON-RPC API"""
    
    def __init__(self, url: str, db: str, username: str, password: str):
        self.url = url.rstrip('/')
        self.db = db
        self.username = username
        self.password = password
        self.uid: Optional[int] = None
        self.session = requests.Session()
        
    def authenticate(self) -> bool:
        """Authenticate with Odoo and get user ID"""
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
                logger.info(f"Authenticated successfully with Odoo (UID: {self.uid})")
                return True
            else:
                logger.error("Authentication failed: Invalid credentials")
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
                logger.error(f"Odoo error: {error_msg}")
                raise Exception(f"Odoo error: {error_msg}")
            
            return result.get('result')
            
        except Exception as e:
            logger.error(f"Execute error: {e}")
            raise
    
    def search_read(self, model: str, domain: list = None, fields: list = None, limit: int = 80) -> list:
        """Search and read records from Odoo"""
        return self.execute_kw(
            model, 
            'search_read', 
            [domain or []], 
            {'fields': fields, 'limit': limit}
        )
    
    def create(self, model: str, values: dict) -> int:
        """Create a record in Odoo"""
        return self.execute_kw(model, 'create', [values])
    
    def write(self, model: str, ids: list, values: dict) -> bool:
        """Update records in Odoo"""
        return self.execute_kw(model, 'write', [ids, values])
    
    def unlink(self, model: str, ids: list) -> bool:
        """Delete records from Odoo"""
        return self.execute_kw(model, 'unlink', [ids])
    
    # Accounting Methods
    def get_invoices(self, invoice_type: str = 'out_invoice', limit: int = 50) -> list:
        """Get invoices from Odoo"""
        domain = [('move_type', '=', invoice_type)]
        fields = ['id', 'name', 'partner_id', 'invoice_date', 'amount_total', 
                  'amount_residual', 'state', 'payment_state']
        return self.search_read('account.move', domain, fields, limit)
    
    def get_invoice(self, invoice_id: int) -> dict:
        """Get single invoice details"""
        domain = [('id', '=', invoice_id)]
        fields = ['id', 'name', 'partner_id', 'invoice_date', 'invoice_date_due',
                  'amount_total', 'amount_residual', 'state', 'payment_state', 
                  'narration', 'invoice_line_ids']
        result = self.search_read('account.move', domain, fields, 1)
        return result[0] if result else None
    
    def create_invoice(self, partner_id: int, invoice_lines: list, 
                      invoice_date: str = None, payment_term: int = None) -> int:
        """Create a new customer invoice"""
        values = {
            'move_type': 'out_invoice',
            'partner_id': partner_id,
            'invoice_line_ids': invoice_lines,
            'invoice_date': invoice_date,
            'invoice_payment_term_id': payment_term
        }
        # Remove None values
        values = {k: v for k, v in values.items() if v is not None}
        return self.create('account.move', values)
    
    def validate_invoice(self, invoice_id: int) -> bool:
        """Post/validate an invoice"""
        return self.execute_kw('account.move', 'action_post', [[invoice_id]])
    
    def get_payments(self, limit: int = 50) -> list:
        """Get payment records"""
        domain = []
        fields = ['id', 'name', 'partner_id', 'date', 'amount', 
                  'payment_type', 'state', 'journal_id']
        return self.search_read('account.payment', domain, fields, limit)
    
    def register_payment(self, invoice_id: int, amount: float, 
                        payment_date: str = None, journal_id: int = None) -> int:
        """Register payment for an invoice"""
        # Create payment wizard
        wizard_values = {
            'amount': amount,
            'payment_date': payment_date,
            'journal_id': journal_id,
        }
        wizard_values = {k: v for k, v in wizard_values.items() if v is not None}
        
        # This is simplified - actual implementation needs payment wizard
        logger.info(f"Registering payment of {amount} for invoice {invoice_id}")
        return invoice_id
    
    def get_account_moves(self, domain: list = None, limit: int = 100) -> list:
        """Get accounting entries"""
        fields = ['id', 'name', 'date', 'account_id', 'debit', 'credit', 
                  'balance', 'partner_id', 'state']
        return self.search_read('account.move.line', domain or [], fields, limit)
    
    def get_trial_balance(self) -> list:
        """Get trial balance report"""
        # This would typically use Odoo's report engine
        # Simplified version - get all accounts with balances
        domain = [('parent_id', '!=', False)]
        fields = ['code', 'name', 'balance']
        return self.search_read('account.account', domain, fields)
    
    # Partner (Customer/Vendor) Methods
    def get_partners(self, domain: list = None, limit: int = 100) -> list:
        """Get partners (customers/vendors)"""
        fields = ['id', 'name', 'email', 'phone', 'street', 'city', 
                  'country_id', 'vat', 'customer_rank', 'supplier_rank']
        return self.search_read('res.partner', domain or [], fields, limit)
    
    def create_partner(self, name: str, email: str = None, phone: str = None,
                      is_customer: bool = True, is_supplier: bool = False) -> int:
        """Create a new partner"""
        values = {
            'name': name,
            'email': email,
            'phone': phone,
            'customer_rank': 1 if is_customer else 0,
            'supplier_rank': 1 if is_supplier else 0
        }
        return self.create('res.partner', values)
    
    # Product Methods
    def get_products(self, domain: list = None, limit: int = 100) -> list:
        """Get products"""
        fields = ['id', 'name', 'default_code', 'list_price', 'cost', 
                  'type', 'categ_id', 'taxes_id']
        return self.search_read('product.template', domain or [], fields, limit)
    
    def create_product(self, name: str, list_price: float, cost: float = 0.0,
                      product_type: str = 'product') -> int:
        """Create a new product"""
        values = {
            'name': name,
            'list_price': list_price,
            'cost': cost,
            'type': product_type
        }
        return self.create('product.template', values)
    
    # Company Methods
    def get_company_info(self) -> dict:
        """Get current company information"""
        if not self.uid:
            self.authenticate()
        
        result = self.search_read('res.company', [], ['name', 'vat', 'street', 
                                                       'city', 'country_id', 
                                                       'phone', 'email'], 1)
        return result[0] if result else None
    
    # Report Methods
    def get_financial_summary(self, month: int = None, year: int = None) -> dict:
        """Get financial summary for the period"""
        from datetime import datetime
        
        if month is None or year is None:
            now = datetime.now()
            month = now.month
            year = now.year
        
        # Get invoices for the period
        domain = [
            ('move_type', 'in', ['out_invoice', 'in_invoice']),
            ('invoice_date', '>=', f'{year}-{month:02d}-01'),
            ('invoice_date', '<=', f'{year}-{month:02d}-31'),
            ('state', '=', 'posted')
        ]
        
        invoices = self.search_read('account.move', domain, 
                                   ['amount_total', 'amount_residual', 'move_type'])
        
        summary = {
            'period': f'{year}-{month:02d}',
            'total_revenue': 0.0,
            'total_expenses': 0.0,
            'total_receivable': 0.0,
            'total_payable': 0.0,
            'invoice_count': 0,
            'vendor_bill_count': 0
        }
        
        for invoice in invoices:
            if invoice['move_type'] == 'out_invoice':
                summary['total_revenue'] += invoice['amount_total'] or 0
                summary['total_receivable'] += invoice['amount_residual'] or 0
                summary['invoice_count'] += 1
            else:
                summary['total_expenses'] += invoice['amount_total'] or 0
                summary['total_payable'] += invoice['amount_residual'] or 0
                summary['vendor_bill_count'] += 1
        
        return summary


# Initialize Odoo client
odoo_client = OdooClient(ODOO_URL, ODOO_DB, ODOO_USERNAME, ODOO_PASSWORD)

# Create MCP server
app = Server("odoo-mcp")


@app.list_tools()
async def list_tools() -> list[Tool]:
    """List available Odoo tools"""
    return [
        Tool(
            name="odoo_authenticate",
            description="Authenticate with Odoo ERP system",
            inputSchema={
                "type": "object",
                "properties": {
                    "username": {"type": "string", "description": "Odoo username"},
                    "password": {"type": "string", "description": "Odoo password"}
                },
                "required": ["username", "password"]
            }
        ),
        Tool(
            name="odoo_get_invoices",
            description="Get invoices from Odoo (customer invoices or vendor bills)",
            inputSchema={
                "type": "object",
                "properties": {
                    "invoice_type": {
                        "type": "string", 
                        "enum": ["out_invoice", "in_invoice"],
                        "description": "Type: out_invoice (customer) or in_invoice (vendor)"
                    },
                    "limit": {"type": "integer", "description": "Maximum number of invoices to return", "default": 50}
                }
            }
        ),
        Tool(
            name="odoo_get_invoice",
            description="Get details of a specific invoice",
            inputSchema={
                "type": "object",
                "properties": {
                    "invoice_id": {"type": "integer", "description": "Invoice ID"}
                },
                "required": ["invoice_id"]
            }
        ),
        Tool(
            name="odoo_create_invoice",
            description="Create a new customer invoice in Odoo",
            inputSchema={
                "type": "object",
                "properties": {
                    "partner_id": {"type": "integer", "description": "Customer ID"},
                    "invoice_lines": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "product_id": {"type": "integer"},
                                "name": {"type": "string"},
                                "quantity": {"type": "number"},
                                "price_unit": {"type": "number"}
                            }
                        },
                        "description": "Invoice line items"
                    },
                    "invoice_date": {"type": "string", "description": "Invoice date (YYYY-MM-DD)"},
                    "payment_term": {"type": "integer", "description": "Payment term ID"}
                },
                "required": ["partner_id", "invoice_lines"]
            }
        ),
        Tool(
            name="odoo_validate_invoice",
            description="Post/validate a draft invoice",
            inputSchema={
                "type": "object",
                "properties": {
                    "invoice_id": {"type": "integer", "description": "Invoice ID to validate"}
                },
                "required": ["invoice_id"]
            }
        ),
        Tool(
            name="odoo_get_payments",
            description="Get payment records from Odoo",
            inputSchema={
                "type": "object",
                "properties": {
                    "limit": {"type": "integer", "description": "Maximum payments to return", "default": 50}
                }
            }
        ),
        Tool(
            name="odoo_get_partners",
            description="Get partners (customers/vendors) from Odoo",
            inputSchema={
                "type": "object",
                "properties": {
                    "partner_type": {
                        "type": "string",
                        "enum": ["customer", "supplier", "all"],
                        "description": "Filter by partner type"
                    },
                    "limit": {"type": "integer", "description": "Maximum partners to return", "default": 100}
                }
            }
        ),
        Tool(
            name="odoo_create_partner",
            description="Create a new partner (customer/vendor) in Odoo",
            inputSchema={
                "type": "object",
                "properties": {
                    "name": {"type": "string", "description": "Partner name"},
                    "email": {"type": "string", "description": "Email address"},
                    "phone": {"type": "string", "description": "Phone number"},
                    "is_customer": {"type": "boolean", "description": "Is a customer", "default": True},
                    "is_supplier": {"type": "boolean", "description": "Is a supplier", "default": False}
                },
                "required": ["name"]
            }
        ),
        Tool(
            name="odoo_get_products",
            description="Get products from Odoo",
            inputSchema={
                "type": "object",
                "properties": {
                    "limit": {"type": "integer", "description": "Maximum products to return", "default": 100}
                }
            }
        ),
        Tool(
            name="odoo_create_product",
            description="Create a new product in Odoo",
            inputSchema={
                "type": "object",
                "properties": {
                    "name": {"type": "string", "description": "Product name"},
                    "list_price": {"type": "number", "description": "Sale price"},
                    "cost": {"type": "number", "description": "Cost price", "default": 0.0},
                    "product_type": {"type": "string", "enum": ["product", "service"], "default": "product"}
                },
                "required": ["name", "list_price"]
            }
        ),
        Tool(
            name="odoo_get_financial_summary",
            description="Get financial summary for a specific period",
            inputSchema={
                "type": "object",
                "properties": {
                    "month": {"type": "integer", "description": "Month (1-12)", "minimum": 1, "maximum": 12},
                    "year": {"type": "integer", "description": "Year"}
                }
            }
        ),
        Tool(
            name="odoo_get_company_info",
            description="Get current company information",
            inputSchema={
                "type": "object",
                "properties": {}
            }
        ),
        Tool(
            name="odoo_execute_kw",
            description="Execute custom Odoo ORM operation (advanced users)",
            inputSchema={
                "type": "object",
                "properties": {
                    "model": {"type": "string", "description": "Odoo model name"},
                    "method": {"type": "string", "description": "ORM method to call"},
                    "args": {"type": "array", "description": "Method arguments"},
                    "kwargs": {"type": "object", "description": "Method keyword arguments"}
                },
                "required": ["model", "method"]
            }
        )
    ]


@app.call_tool()
async def call_tool(name: str, arguments: dict) -> list[TextContent]:
    """Execute Odoo tool"""
    try:
        result = None
        
        if name == "odoo_authenticate":
            success = odoo_client.authenticate()
            result = {"success": success, "uid": odoo_client.uid if success else None}
            
        elif name == "odoo_get_invoices":
            invoice_type = arguments.get('invoice_type', 'out_invoice')
            limit = arguments.get('limit', 50)
            result = odoo_client.get_invoices(invoice_type, limit)
            
        elif name == "odoo_get_invoice":
            invoice_id = arguments.get('invoice_id')
            result = odoo_client.get_invoice(invoice_id)
            
        elif name == "odoo_create_invoice":
            partner_id = arguments.get('partner_id')
            invoice_lines = arguments.get('invoice_lines')
            invoice_date = arguments.get('invoice_date')
            payment_term = arguments.get('payment_term')
            
            invoice_id = odoo_client.create_invoice(
                partner_id, invoice_lines, invoice_date, payment_term
            )
            result = {"success": True, "invoice_id": invoice_id}
            
        elif name == "odoo_validate_invoice":
            invoice_id = arguments.get('invoice_id')
            success = odoo_client.validate_invoice(invoice_id)
            result = {"success": success}
            
        elif name == "odoo_get_payments":
            limit = arguments.get('limit', 50)
            result = odoo_client.get_payments(limit)
            
        elif name == "odoo_get_partners":
            partner_type = arguments.get('partner_type', 'all')
            limit = arguments.get('limit', 100)
            
            domain = []
            if partner_type == 'customer':
                domain = [('customer_rank', '>', 0)]
            elif partner_type == 'supplier':
                domain = [('supplier_rank', '>', 0)]
                
            result = odoo_client.get_partners(domain, limit)
            
        elif name == "odoo_create_partner":
            name = arguments.get('name')
            email = arguments.get('email')
            phone = arguments.get('phone')
            is_customer = arguments.get('is_customer', True)
            is_supplier = arguments.get('is_supplier', False)
            
            partner_id = odoo_client.create_partner(name, email, phone, is_customer, is_supplier)
            result = {"success": True, "partner_id": partner_id}
            
        elif name == "odoo_get_products":
            limit = arguments.get('limit', 100)
            result = odoo_client.get_products(limit=limit)
            
        elif name == "odoo_create_product":
            name = arguments.get('name')
            list_price = arguments.get('list_price')
            cost = arguments.get('cost', 0.0)
            product_type = arguments.get('product_type', 'product')
            
            product_id = odoo_client.create_product(name, list_price, cost, product_type)
            result = {"success": True, "product_id": product_id}
            
        elif name == "odoo_get_financial_summary":
            month = arguments.get('month')
            year = arguments.get('year')
            result = odoo_client.get_financial_summary(month, year)
            
        elif name == "odoo_get_company_info":
            result = odoo_client.get_company_info()
            
        elif name == "odoo_execute_kw":
            model = arguments.get('model')
            method = arguments.get('method')
            args = arguments.get('args', [])
            kwargs = arguments.get('kwargs', {})
            
            result = odoo_client.execute_kw(model, method, args, kwargs)
        
        else:
            return [TextContent(type="text", text=f"Unknown tool: {name}")]
        
        return [TextContent(type="text", text=json.dumps(result, indent=2, default=str))]
        
    except Exception as e:
        logger.error(f"Tool execution error: {e}")
        return [TextContent(type="text", text=f"Error: {str(e)}")]


async def main():
    """Run the MCP server"""
    logger.info("Starting Odoo MCP Server...")
    
    # Try to authenticate on startup
    if odoo_client.authenticate():
        logger.info("Successfully connected to Odoo")
    else:
        logger.warning("Could not connect to Odoo - will retry on first request")
    
    async with stdio_server() as (read_stream, write_stream):
        await app.run(
            read_stream,
            write_stream,
            app.create_initialization_options()
        )


if __name__ == "__main__":
    asyncio.run(main())
