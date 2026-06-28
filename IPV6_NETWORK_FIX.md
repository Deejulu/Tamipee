# IPv6 Network Issue Fix

## Problem: "Network is unreachable" with IPv6 Address

### Error Signature:
```
django.db.utils.OperationalError: connection is bad: 
connection to server at "2a05:d018:f3f:3100:bedc:bad0:57bf:e7e7", port 5432 failed: 
Network is unreachable
```

### Root Cause:
Render's network infrastructure **does not support IPv6** connections, but Supabase's DNS may return IPv6 addresses (AAAA records) before IPv4 addresses (A records). When psycopg (PostgreSQL driver) attempts to connect using IPv6, the connection fails.

---

## ✅ Solution (Already Implemented)

The codebase now includes automatic IPv4-only resolution in [tamipee/settings.py](tamipee/settings.py):

### What It Does:
1. **Resolves hostname to IPv4**: Uses Python's `socket.getaddrinfo()` with `AF_INET` flag
2. **Replaces HOST with IP**: Changes `db.lzsimijosxbarnstgkyb.supabase.co` → `54.x.x.x`
3. **Forces SSL**: Adds `sslmode=require` to connection options
4. **Timeout protection**: Sets 10-second connection timeout

### Code Implementation:
```python
# In tamipee/settings.py (lines ~140-165)
if DATABASE_URL:
    DATABASES['default'] = dj_database_url.parse(DATABASE_URL, ...)
    
    # Force IPv4 connection (Render doesn't support IPv6)
    original_host = DATABASES['default'].get('HOST', '')
    if original_host:
        try:
            # Resolve hostname to IPv4 address only
            ipv4_address = socket.getaddrinfo(
                original_host, 
                None, 
                socket.AF_INET,  # Force IPv4
                socket.SOCK_STREAM
            )[0][4][0]
            DATABASES['default']['HOST'] = ipv4_address
            print(f"✓ Resolved {original_host} to IPv4: {ipv4_address}")
        except socket.gaierror as e:
            print(f"⚠ Could not resolve {original_host} to IPv4: {e}")
```

---

## 🔍 Verify Fix is Working

### In Render Deployment Logs:

**✅ Success Looks Like:**
```
--- start.sh diagnostics ---
PWD=/opt/render/project/src
DJANGO_SETTINGS_MODULE=tamipee.settings
Validating DATABASE_URL format...
✓ DATABASE_URL validation passed
  Host: db.lzsimijosxbarnstgkyb.supabase.co
  Port: 5432
  User: postgres
  Database: postgres

✓ Resolved db.lzsimijosxbarnstgkyb.supabase.co to IPv4: 54.85.123.45

Collecting static...
[... static files collected ...]
Running migrations...
Operations to perform:
  Apply all migrations: admin, auth, contenttypes, sessions, accounts, livestock, store, payments
Running migrations:
  No migrations to apply.

[INFO] Starting gunicorn 21.2.0
[INFO] Listening at: http://0.0.0.0:10000 (pid: 123)
```

**❌ Still Failing Looks Like:**
```
⚠ Could not resolve db.lzsimijosxbarnstgkyb.supabase.co to IPv4: [Errno -2] Name or service not known

# OR

django.db.utils.OperationalError: connection is bad: 
connection to server at "2a05:d018:..." failed: Network is unreachable
```

---

## 🛠️ Troubleshooting

### If Still Getting IPv6 Errors:

#### 1. Check DATABASE_URL Format
Ensure your DATABASE_URL in Render environment variables is:
```
postgresql://postgres:tamipee00%4011@db.lzsimijosxbarnstgkyb.supabase.co:5432/postgres?sslmode=require
```

**Key Points:**
- ✅ Password encoded: `tamipee00@11` → `tamipee00%4011`
- ✅ Port: `5432` (Direct Connection)
- ✅ SSL parameter: `?sslmode=require` at end
- ✅ Username: `postgres` (NOT `postgres.PROJECT_REF`)

#### 2. Verify Supabase Project Status
1. Go to [Supabase Dashboard](https://supabase.com/dashboard)
2. Select project: `lzsimijosxbarnstgkyb`
3. **If paused**: Click "Resume Project" button
4. Wait 1-2 minutes for database to wake up

#### 3. Check Render Redeploy
After setting DATABASE_URL:
1. Render should auto-redeploy (check "Events" tab)
2. If not, manually trigger: **Manual Deploy** → **Deploy latest commit**
3. Monitor logs for IPv4 resolution message

#### 4. DNS Resolution Issues
If you see `Name or service not known`:
- **Cause**: Render's build environment can't resolve Supabase hostname
- **Fix**: Add Google DNS to help resolve:
  - In Render → Environment → Add variable:
    - Key: `DNS_SERVERS`
    - Value: `8.8.8.8,8.8.4.4`

---

## 📋 Complete Deployment Checklist

Before deploying, ensure:

- [ ] Supabase project is **resumed** (not paused)
- [ ] DATABASE_URL uses **Direct Connection** format (port 5432)
- [ ] Password is **URL-encoded** (`@` → `%40`)
- [ ] DATABASE_URL ends with `?sslmode=require`
- [ ] Latest code is pushed to GitHub (`git push origin main`)
- [ ] Render is set to **Auto-Deploy** from `main` branch

---

## 🎯 Why This Happens

### Technical Background:
1. **DNS Resolution Order**: Modern systems prefer IPv6 (AAAA records) over IPv4 (A records)
2. **Supabase DNS**: Returns both IPv6 and IPv4 addresses
3. **psycopg Behavior**: Tries to connect to first resolved address (often IPv6)
4. **Render Network**: Doesn't have IPv6 routing configured
5. **Result**: Connection attempt to IPv6 address fails with "Network is unreachable"

### The Fix:
By forcing `socket.AF_INET` (IPv4-only) during DNS resolution, we guarantee psycopg only sees IPv4 addresses, avoiding the IPv6 connection attempt entirely.

---

## 📚 Related Documentation

- [RENDER_DATABASE_FIX.md](RENDER_DATABASE_FIX.md) - General database connection troubleshooting
- [DEPLOYMENT.md](DEPLOYMENT.md) - Full deployment guide
- [Supabase Direct Connection](https://supabase.com/docs/guides/database/connecting-to-postgres#direct-connections)
- [psycopg Connection Parameters](https://www.psycopg.org/psycopg3/docs/api/connections.html)

---

**Fix Deployed**: Commit `943c836` (2026-06-28)  
**Status**: Active in production
