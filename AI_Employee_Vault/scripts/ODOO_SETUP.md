# Odoo ERP Configuration Guide
## Gold Tier - Personal AI FTEs Project

This guide walks you through setting up Odoo Community Edition for the Odoo MCP Server.

---

## Quick Start

```bash
# 1. Start Odoo with Docker
cd D:\Personal-AI-FTEs\docker
docker-compose up -d

# 2. Wait for Odoo to start (2-3 minutes)
docker-compose logs -f odoo

# 3. Access Odoo in browser
# http://localhost:8069
```

---

## Step 1: Start Odoo Docker Stack

```bash
cd D:\Personal-AI-FTEs\docker

# Start all services
docker-compose up -d

# Check status
docker-compose ps
```

Expected output:
```
NAME                STATUS              PORTS
odoo_community      Up (healthy)        0.0.0.0:8069->8069/tcp
odoo_postgres       Up (healthy)        5432/tcp
odoo_redis          Up (healthy)        6379/tcp
```

---

## Step 2: Access Odoo Web Interface

1. Open browser: http://localhost:8069
2. Default credentials:
   ```
   Email: admin
   Password: admin
   ```
3. **IMPORTANT:** Change password immediately!

---

## Step 3: Configure Odoo Database

### Create New Database (if needed)

1. Go to http://localhost:8069/web/database/manager
2. Click **"Create Database"**
3. Fill in:
   ```
   Master Password: odoo_secure_admin_password_123  (from docker/.env)
   Database Name: postgres
   Email: your-email@example.com
   Password: your_new_secure_password
   ```

---

## Step 4: Install Required Odoo Apps

1. Go to **Apps** menu
2. Install these modules:
   - ✅ **Invoicing** (accounting features)
   - ✅ **Contacts** (partner management)
   - ✅ **Products** (product catalog)

---

## Step 5: Configure Company Information

1. Go to **Settings → Companies**
2. Update your company details:
   - Company name
   - Address
   - Tax ID
   - Currency

---

## Step 6: Create Test Customer

1. Go to **Contacts → Create**
2. Fill in:
   ```
   Name: Test Client Corp
   Email: billing@testclient.com
   Phone: +1-234-567-8900
   Address: 123 Business St, City, Country
   ```
3. Set as Customer: ✅ Checked
4. Save

---

## Step 7: Create Test Product

1. Go to **Invoicing → Products → Create**
2. Fill in:
   ```
   Product Name: Consulting Services
   Product Type: Service
   Sales Price: $150.00
   Tax: As per your location
   ```
3. Save

---

## Step 8: Update .env File

Navigate to `D:\Personal-AI-FTEs\AI_Employee_Vault\scripts\` and edit `.env`:

```bash
# Odoo ERP Configuration
ODOO_URL=http://localhost:8069
ODOO_DB=postgres
ODOO_USERNAME=admin
ODOO_PASSWORD=your_new_password  # ← Change this!
```

---

## Step 9: Test Odoo Connection

```bash
cd D:\Personal-AI-FTEs\AI_Employee_Vault\scripts

# Test Odoo MCP server
python odoo_mcp_server.py
```

Expected output:
```
INFO:odoo-mcp:Starting Odoo MCP Server...
INFO:odoo-mcp:Successfully connected to Odoo (UID: 2)
```

---

## Step 10: Test in Claude Code

```bash
# Get company info
@odoo odoo_get_company_info

# Get partners (customers)
@odoo odoo_get_partners partner_type="customer" limit=10

# Create invoice
@odoo odoo_create_invoice 
  partner_id=1 
  invoice_lines=[{"name": "Consulting", "quantity": 10, "price_unit": 150}]

# Get invoices
@odoo odoo_get_invoices invoice_type="out_invoice" limit=5

# Get financial summary
@odoo odoo_get_financial_summary month=3 year=2026
```

---

## Odoo Watcher Configuration

The Odoo Watcher monitors for:

- Overdue invoices (> 7 days)
- Unpaid vendor bills
- Large transactions (> $5,000)
- Low bank balance (< $1,000)
- Draft invoices awaiting approval

### Start Odoo Watcher

```bash
cd D:\Personal-AI-FTEs\AI_Employee_Vault\scripts

# Run once
python odoo_watcher.py

# Or use PM2 for always-on
pm2 start odoo_watcher.py --interpreter python --name odoo-watcher
pm2 save
```

---

## Common Odoo MCP Operations

### Create Customer
```bash
@odoo odoo_create_partner 
  name="Acme Corporation" 
  email="info@acme.com" 
  phone="+1-555-123-4567"
  is_customer=true
```

### Create Product
```bash
@odoo odoo_create_product 
  name="Web Development Service" 
  list_price=100 
  cost=0 
  product_type="service"
```

### Create and Send Invoice
```bash
# 1. Create invoice
@odoo odoo_create_invoice 
  partner_id=1 
  invoice_lines=[{"name": "Service", "quantity": 1, "price_unit": 1000}]

# 2. Validate (post) invoice
@odoo odoo_validate_invoice invoice_id=123
```

### Get Financial Summary
```bash
@odoo odoo_get_financial_summary month=3 year=2026
```

---

## Troubleshooting

### Odoo Won't Start

```bash
# Check logs
docker-compose logs odoo

# Restart Odoo
docker-compose restart odoo

# Check port 8069
netstat -ano | findstr :8069
```

### Authentication Failed

1. Verify credentials in `.env`
2. Check Odoo user exists:
   ```bash
   docker exec -it odoo_postgres psql -U odoo -c "SELECT id, login FROM res_users"
   ```
3. Reset password in Odoo UI: Settings → Users

### Database Connection Error

```bash
# Check PostgreSQL is running
docker-compose ps db

# Restart database
docker-compose restart db
```

### MCP Connection Issues

```bash
# Test Odoo directly
curl http://localhost:8069

# Should return Odoo homepage
```

---

## Backup Strategy

### Daily Backup Script

```bash
# backup_odoo.sh
cd D:\Personal-AI-FTEs\docker

# Backup database
docker exec odoo_postgres pg_dump -U odoo postgres > backup_$(date +%Y%m%d).sql

# Backup filestore
docker run --rm -v odoo-web-data:/data -v .:/backup alpine \
  tar czf /backup/web-data-$(date +%Y%m%d).tar.gz /data
```

### Schedule with Windows Task Scheduler

1. Open Task Scheduler
2. Create Basic Task
3. Set daily trigger (2:00 AM)
4. Action: Start a program
   ```
   Program: C:\Windows\System32\bash.exe
   Arguments: -c "cd /d/Personal-AI-FTEs/docker && ./backup_odoo.sh"
   ```

---

## Security Best Practices

1. **Change default admin password** immediately
2. **Use strong passwords** (12+ characters)
3. **Enable HTTPS** in production (nginx config provided)
4. **Regular backups** (daily recommended)
5. **Update Odoo** monthly for security patches
6. **Restrict database access** to localhost
7. **Use separate database user** for Odoo

---

## Production Deployment

For production use:

1. **Enable HTTPS** in nginx configuration
2. **Set strong master password** in `odoo.conf`
3. **Configure email** for invoices
4. **Set up automated backups**
5. **Monitor disk space** (logs can grow large)
6. **Use external database** for better performance

---

## Quick Reference

### Default Credentials
```
Database: postgres
Username: admin
Password: admin  ← CHANGE THIS!
```

### Important URLs
```
Odoo Web: http://localhost:8069
Database Manager: http://localhost:8069/web/database/manager
```

### Docker Commands
```bash
# Start
docker-compose up -d

# Stop
docker-compose down

# Restart
docker-compose restart

# Logs
docker-compose logs -f odoo

# Status
docker-compose ps
```

### Environment Variables
```bash
ODOO_URL=http://localhost:8069
ODOO_DB=postgres
ODOO_USERNAME=admin
ODOO_PASSWORD=your_password
```

---

**Date:** 2026-03-25  
**Version:** 1.0  
**Status:** Ready for Configuration
