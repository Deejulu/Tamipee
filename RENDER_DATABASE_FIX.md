# Quick Fix: Render Database Connection Error

## Your Current Error

```
django.db.utils.OperationalError: connection failed: 
FATAL: (ENOTFOUND) tenant/user postgres.lzsimijosxbarnstgkyb not found
```

## What's Wrong

Your `DATABASE_URL` environment variable in Render is using the **wrong format** for Supabase pooler connection, or the credentials don't match your Supabase project.

## How to Fix (Step-by-Step)

### Step 1: Get the Correct Connection String

#### If Using Supabase:

1. Go to [Supabase Dashboard](https://supabase.com/dashboard)
2. Select your project
3. Click **Project Settings** (gear icon) → **Database**
4. Scroll to **Connection string** section
5. Click **URI** tab
6. **IMPORTANT**: Make sure you're looking at **Direct connection**, NOT "Connection pooling"
7. Copy the string that looks like:
   ```
   postgresql://postgres:[YOUR-PASSWORD]@db.abcdefg123.supabase.co:5432/postgres
   ```
8. Replace `[YOUR-PASSWORD]` with your actual database password

#### Password Has Special Characters?

If your password contains `@`, `:`, `/`, `%`, or `#`, you MUST encode them:

| Character | Encoded |
|-----------|---------|
| `@` | `%40` |
| `:` | `%3A` |
| `/` | `%2F` |
| `%` | `%25` |
| `#` | `%23` |

**Example**:
- Password: `MyP@ss:123`
- In URL: `MyP%40ss%3A123`

#### If Using Render PostgreSQL:

1. Go to [Render Dashboard](https://dashboard.render.com)
2. Click on your PostgreSQL database (not the web service)
3. Copy the **Internal Database URL** (starts with `postgresql://`)
4. Use it exactly as-is

### Step 2: Update DATABASE_URL in Render

1. Go to [Render Dashboard](https://dashboard.render.com)
2. Click on your **web service** (e.g., "tamipee-farms")
3. Go to **Environment** tab (left sidebar)
4. Find `DATABASE_URL` variable
5. Click **Edit** (pencil icon)
6. **Paste the correct connection string** (from Step 1)
7. **DO NOT add quotes** around the value
8. Click **Save Changes**

### Step 3: Verify the Fix

After saving, Render will automatically redeploy. Monitor the logs:

1. Go to **Logs** tab in your Render service
2. Look for these lines early in the deployment:

**✅ Success looks like**:
```
Validating DATABASE_URL format...
✓ DATABASE_URL validation passed
  Host: db.abcdefg123.supabase.co
  Port: 5432
  User: postgres
  Database: postgres
```

**❌ Failure looks like**:
```
ERROR: Supabase pooler connection requires username format 'postgres.[PROJECT_REF]'
Current username: 'postgres.wrongref'
```

### Step 4: Deployment Should Succeed

After successful validation, you'll see:
```
Collecting static...
[... static files collected ...]
Operations to perform:
  Apply all migrations: [...]
Running migrations:
  No migrations to apply.
Starting gunicorn...
```

## Still Not Working?

### Double-Check These:

1. **No quotes**: `DATABASE_URL=postgresql://...` (NOT `DATABASE_URL="postgresql://..."`)
2. **Correct password**: Make sure you're using the actual database password
3. **Special characters encoded**: If password has `@`, `:`, etc., they must be encoded
4. **Correct connection type**: Use **Direct Connection** for Supabase, NOT Pooler
5. **Project matches**: If using Supabase, the project reference in the URL must match your actual project

### Test Locally First (Optional)

If you want to verify the connection string works before deploying:

1. On your local machine, activate your virtual environment
2. Set the DATABASE_URL temporarily:
   ```powershell
   $env:DATABASE_URL = "postgresql://postgres:password@db.abc.supabase.co:5432/postgres"
   ```
3. Run migrations:
   ```powershell
   python manage.py migrate
   ```
4. If migrations work locally, the same URL will work on Render

## Quick Reference: Correct DATABASE_URL Formats

### Render PostgreSQL (Recommended)
```
postgresql://user_abc123:pass_xyz@postgres-host.render.com/db_name
```
- Copy directly from Render PostgreSQL dashboard → Internal Database URL

### Supabase (Direct Connection - Recommended)
```
postgresql://postgres:YOUR_PASSWORD@db.PROJECT_REF.supabase.co:5432/postgres
```
- From Supabase Dashboard → Settings → Database → Connection string → URI (Direct)

### Supabase (Pooler - NOT RECOMMENDED for Django)
```
postgresql://postgres.PROJECT_REF:YOUR_PASSWORD@aws-0-REGION.pooler.supabase.com:6543/postgres
```
- ⚠️ Can cause compatibility issues; use Direct Connection instead

## After Fix: Next Steps

Once deployment succeeds:

1. Visit your app URL: `https://your-app.onrender.com`
2. Verify homepage loads
3. Test login/register functionality
4. Access admin panel: `https://your-app.onrender.com/admin/`

## Need More Help?

See full deployment guide: [DEPLOYMENT.md](DEPLOYMENT.md)
