# Odoo MCP Integration - Gold Tier Feature

## Overview

This MCP (Model Context Protocol) server integrates your Personal AI FTE with **Odoo Community Edition 18+** ERP system. It enables autonomous accounting, invoicing, and business operations through **Qwen Code**.

## Quick Start

```bash
cd D:\Personal-AI-FTEs\.qwen\skills\odoo-mcp

# Authenticate
python odoo.py auth

# Get company info
python odoo.py company

# List customers
python odoo.py customers

# List invoices
python odoo.py invoices

# Get financial summary
python odoo.py summary

# Full help
python odoo.py help
```

## Architecture

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│   Qwen Code     │────▶│  Odoo MCP Server│────▶│  Odoo Community │
│   (AI Reasoning)│◀────│  (JSON-RPC API) │◀────│  (ERP System)   │
└─────────────────┘     └─────────────────┘     └─────────────────┘
```

## Prerequisites

1. **Docker Desktop** installed and running
2. **Python 3.13+** with pip
3. **Odoo 19+** running via Docker Compose (see `docker/docker-compose.yml`)

## Setup Instructions

### Step 1: Start Odoo with Docker Compose

```bash
cd D:\Personal-AI-FTEs\docker

# Copy environment template
copy .env.example .env

# Edit .env and update credentials

# Start Odoo stack
docker-compose up -d

# Verify Odoo is running
docker-compose ps
```

### Step 2: Install Odoo MCP Dependencies

```bash
cd D:\Personal-AI-FTEs\AI_Employee_Vault\scripts

# Install requirements
pip install -r odoo_requirements.txt
```

### Step 3: Configure Odoo MCP Server

Create `.env` file in `D:\Personal-AI-FTEs\.qwen\skills\odoo-mcp\` or update `D:\Personal-AI-FTEs\AI_Employee_Vault\scripts\.env`:

```bash
ODOO_URL=http://localhost:8069
ODOO_DB=odoo
ODOO_USERNAME=your-email@example.com  # The email you used during Odoo setup
ODOO_PASSWORD=your-password           # The password you set
```

**Note:** The database name is `odoo` (not `postgres`) after first-time setup.

### Step 4: Register MCP Server with Qwen Code

**Qwen Code automatically discovers MCP servers** from the `.qwen/skills/` directory. The Odoo MCP server is already in the correct location:

```
D:\Personal-AI-FTEs\.qwen\skills\odoo-mcp/
├── odoo_mcp_server.py    # MCP server
├── odoo.py               # CLI helper
├── mcp-client.py         # MCP client
├── .env                  # Credentials
└── SKILL.md              # This documentation
```

To use Odoo in Qwen Code, simply reference it with `@odoo`:

```
@odoo odoo_get_company_info
```

**Alternative:** If you want to use the scripts folder location, ensure the `.env` file has the correct credentials.

### Step 5: Verify Connection

```bash
# Test Odoo is accessible
curl http://localhost:8069

# Should return Odoo homepage or login page
```

## Available Tools

| Tool | Description | Example |
|------|-------------|---------|
| `odoo_authenticate` | Authenticate with Odoo | Connect to ERP |
| `odoo_get_invoices` | Get customer/vendor invoices | List all unpaid invoices |
| `odoo_get_invoice` | Get specific invoice details | View invoice #123 |
| `odoo_create_invoice` | Create new customer invoice | Generate invoice for client |
| `odoo_validate_invoice` | Post/validate draft invoice | Confirm invoice |
| `odoo_get_payments` | Get payment records | View recent payments |
| `odoo_get_partners` | Get customers/vendors | List all customers |
| `odoo_create_partner` | Create new partner | Add new customer |
| `odoo_get_products` | Get product catalog | List all products |
| `odoo_create_product` | Create new product | Add service/product |
| `odoo_get_financial_summary` | Get financial report | Monthly revenue/expenses |
| `odoo_get_company_info` | Get company details | View company profile |
| `odoo_execute_kw` | Execute custom ORM operations | Advanced operations |

## CLI Helper Script

The `odoo.py` script provides easy command-line access to common Odoo operations.

### Authentication

```bash
python odoo.py auth
```

### Company & Partners

```bash
# Get company information
python odoo.py company

# List all partners
python odoo.py partners

# List customers only
python odoo.py customers [limit]

# List suppliers only
python odoo.py partners supplier [limit]

# Create a new partner
python odoo.py create-partner "Acme Corp" --email="info@acme.com" --phone="+1-555-1234"
```

### Products

```bash
# List products
python odoo.py products [limit]

# Create a new product
python odoo.py create-product "Consulting Service" 150 --type="service" --cost=0
```

### Invoices

```bash
# List customer invoices
python odoo.py invoices [limit]

# List vendor bills
python odoo.py bills [limit]

# Get specific invoice
python odoo.py invoice <invoice_id>

# Validate/post invoice
python odoo.py validate <invoice_id>
```

### Payments

```bash
# List recent payments
python odoo.py payments [limit]
```

### Financial Reports

```bash
# Get current month summary
python odoo.py summary

# Get specific month summary
python odoo.py summary <month> <year>
# Example: python odoo.py summary 3 2026
```

### Using with Qwen Code

In Qwen Code, the MCP server is automatically loaded when you start a session. You can use the Odoo tools directly:

```
# Get company info
@odoo odoo_get_company_info

# Get customers
@odoo odoo_get_partners partner_type="customer" limit=10

# Create invoice
@odoo odoo_create_invoice partner_id=1 invoice_lines=[{"name": "Service", "quantity": 1, "price_unit": 100}]
```

**Note:** Qwen Code will automatically start the MCP server when you reference `@odoo`.

## Usage Examples

### Example 1: Create and Send Invoice

```markdown
// Create a new customer
@odoo create_partner name="Acme Corp" email="billing@acme.com" is_customer=true

// Create invoice for the customer
@odoo create_invoice partner_id=1 invoice_lines=[{"name": "Consulting Services", "quantity": 10, "price_unit": 150}]

// Validate the invoice
@odoo validate_invoice invoice_id=123
```

### Example 2: Get Financial Summary

```markdown
// Get this month's financial summary
@odoo get_financial_summary month=3 year=2026

// Output shows:
// - Total revenue
// - Total expenses
// - Accounts receivable
// - Accounts payable
```

### Example 3: Weekly Accounting Audit

```markdown
// Weekly Business Audit Workflow

// 1. Get all unpaid customer invoices
@odoo get_invoices invoice_type="out_invoice" limit=100

// 2. Get all vendor bills
@odoo get_invoices invoice_type="in_invoice" limit=50

// 3. Get recent payments
@odoo get_payments limit=50

// 4. Get financial summary
@odoo get_financial_summary

// 5. Generate CEO Briefing in Obsidian
// (Creates Briefings/YYYY-MM-DD_Weekly_Accounting_Audit.md)
```

## Integration with Watchers

### Odoo Watcher Pattern

The Odoo Watcher monitors accounting events and creates action files:

```python
# odoo_watcher.py
class OdooWatcher(BaseWatcher):
    def check_for_updates(self) -> list:
        # Check for:
        # - Unpaid invoices older than 30 days
        # - New vendor bills requiring approval
        # - Low bank balance alerts
        pass
    
    def create_action_file(self, item) -> Path:
        # Creates file in Needs_Action/
        # e.g., ODOO_OVERDUE_INVOICE_123.md
        pass
```

## Security Considerations

1. **Change default passwords** immediately after Odoo installation
2. **Use environment variables** for credentials (never commit `.env`)
3. **Enable HTTPS** in production (uncomment nginx HTTPS config)
4. **Restrict database access** to localhost only
5. **Regular backups** of Odoo database and filestore
6. **Audit logging** enabled for all financial transactions

## Backup Strategy

```bash
# Backup Odoo database
docker exec odoo_postgres pg_dump -U odoo postgres > backup_$(date +%Y%m%d).sql

# Backup Odoo filestore (attachments, etc.)
docker run --rm -v odoo-web-data:/data -v $(pwd):/backup alpine tar czf /backup/web-data-$(date +%Y%m%d).tar.gz /data

# Automate with cron (daily at 2 AM)
0 2 * * * /path/to/backup_script.sh
```

## Troubleshooting

### Odoo Won't Start

```bash
# Check logs
docker-compose logs odoo

# Restart Odoo
docker-compose restart odoo

# Reset database (WARNING: deletes all data)
docker-compose down -v
docker-compose up -d
```

### MCP Connection Issues

```bash
# Test Odoo connectivity
curl http://localhost:8069/web/session/authenticate \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","method":"call","params":{"db":"postgres","login":"admin","password":"admin"},"id":1}'

# Check MCP server logs
python odoo_mcp_server.py 2>&1 | tee mcp.log
```

### Authentication Failures

1. Verify credentials in `.env` file
2. Check Odoo user exists: `docker exec -it odoo_postgres psql -U odoo -c "SELECT id, login FROM res_users"`
3. Reset admin password in Odoo UI: Settings → Users → Admin

## Gold Tier Integration Checklist

- [ ] Odoo running via Docker Compose
- [ ] MCP server registered with Claude Code
- [ ] Test invoice creation and validation
- [ ] Create Odoo Watcher script
- [ ] Implement weekly accounting audit
- [ ] Set up CEO Briefing generation
- [ ] Configure HITL for payments over threshold
- [ ] Enable audit logging
- [ ] Test backup/restore procedure

## Next Steps

After completing Odoo integration:

1. **Facebook MCP Server** - Social media automation
2. **Weekly Business Audit** - Automated financial reporting
3. **Ralph Wiggum Loop** - Autonomous multi-step task completion
4. **HITL Workflow** - Human approval for sensitive operations

## Resources

- [Odoo 19 External API Documentation](https://www.odoo.com/documentation/19.0/developer/reference/external_api.html)
- [Odoo Community Edition](https://www.odoo.com/page/community)
- [MCP Specification](https://modelcontextprotocol.io/)
- [Docker Compose Reference](https://docs.docker.com/compose/)

---

*Gold Tier Feature - Personal AI FTEs Project*
*Version: 1.0 | Date: 2026-03-24*
