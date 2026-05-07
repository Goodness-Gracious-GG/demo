# Configuration Management Guide

This guide explains how to manage API keys and configuration for the Code Twins backend, and how to troubleshoot common issues.

## Quick Reference

| Task | Command |
|------|---------|
| Start backend (with validation) | `./setup.sh` |
| Test backend connectivity | `./test_backend.sh` |
| Check health status | `curl http://localhost:8000/health` |
| Reload config without restart | `curl -X POST http://localhost:8000/admin/reload-config` |
| View server logs | `tail -f server.log` |

## Understanding the Problem

When you change API keys in `.env`, the backend server **does not automatically pick up the changes** because environment variables are loaded once at startup. This can cause:

- `ERR_CONNECTION_TIMED_OUT` errors from the frontend
- Server returning 500 errors with "API key not valid" messages
- Silent failures where the server appears running but endpoints don't work

## Solution Overview

We've added several tools to help:

1. **`.env.example`** - Template showing all required variables
2. **`setup.sh`** - Validates configuration before starting server
3. **`test_backend.sh`** - Diagnoses connectivity and API key issues
4. **`/health` endpoint** - Real-time service health monitoring
5. **`/admin/reload-config` endpoint** - Reload env vars without restart
6. **Enhanced error messages** - Clear guidance when keys are missing

## Step-by-Step: Changing Your Gemini API Key

### Option A: Full Restart (Recommended for initial setup)

1. Stop the current server:
   ```bash
   pkill -f "uvicorn main:app"
   ```

2. Update your `.env` file:
   ```bash
   nano .env  # or use any editor
   ```
   Change the line:
   ```
   GEMINI_API_KEY=your_new_key_here
   ```

3. Run the setup script to validate and start:
   ```bash
   ./setup.sh
   ```

4. Test with:
   ```bash
   ./test_backend.sh
   ```

### Option B: Hot Reload (No downtime)

If the server is already running and you just need to update the key:

1. Update your `.env` file with the new key

2. Call the reload endpoint:
   ```bash
   curl -X POST http://localhost:8000/admin/reload-config
   ```

3. Verify the change took effect:
   ```bash
   curl http://localhost:8000/health
   ```

4. Test an analyze request:
   ```bash
   curl -X POST http://localhost:8000/analyze \
     -H "Content-Type: application/json" \
     -d '{"code":"print(\"test\")","language":"python"}'
   ```

## Using the Health Check

The `/health` endpoint tells you exactly what's wrong:

```bash
curl http://localhost:8000/health | python3 -m json.tool
```

**Example output when Gemini key is invalid:**
```json
{
  "status": "degraded",
  "services": {
    "gemini": {
      "status": "error",
      "message": "429 RESOURCE_EXHAUSTED..."
    },
    "supabase": {
      "status": "connected"
    }
  }
}
```

**Interpretation:**
- `"status": "healthy"` → All services working
- `"status": "degraded"` → One or more services have issues
- Check each service's `"status"` field for details

## Common Error Messages and Fixes

### "GEMINI_API_KEY is missing"
**Cause**: `.env` file doesn't have the variable set.
**Fix**: Add `GEMINI_API_KEY=your_actual_key` to `.env` and restart server.

### "API key not valid"
**Cause**: The key is malformed or revoked.
**Fix**: Get a new key from [Google AI Studio](https://aistudio.google.com/app/apikey).

### "quota exceeded"
**Cause**: You've hit the free tier limits (20 requests/day for gemini-2.0-flash).
**Fix**:
- Wait for quota to reset (usually in 24 hours)
- Add billing to your Google Cloud project
- Use a different API key

### "SUPABASE_URL and SUPABASE_ANON_KEY must be set"
**Cause**: Backend env vars missing (note: these are different from frontend `VITE_` vars).
**Fix**: Add both `SUPABASE_URL` and `SUPABASE_ANON_KEY` to `.env`.

### Frontend shows "Failed to fetch" but backend works
**Cause**: Missing `VITE_SUPABASE_URL` and `VITE_SUPABASE_ANON_KEY` in `.env`.
**Fix**: Add the Vite-prefixed versions (frontend needs these too).

## Environment Variables Explained

### Backend-Only (loaded by `main.py`)
```
GEMINI_API_KEY=...
SUPABASE_URL=...
SUPABASE_ANON_KEY=...
```

### Frontend-Only (loaded by Vite, exposed to browser)
```
VITE_SUPABASE_URL=...
VITE_SUPABASE_ANON_KEY=...
```

**Note**: The `VITE_` prefix is required by Vite to expose variables to the client. Without these, the frontend JavaScript cannot connect to Supabase even if the backend can.

## Automated Validation

The `setup.sh` script performs these checks:

1. ✅ `.env` file exists
2. ✅ `GEMINI_API_KEY` is set and not a placeholder
3. ✅ `SUPABASE_URL` is set and not a placeholder
4. ✅ `SUPABASE_ANON_KEY` is set and not a placeholder
5. ✅ Warns if `VITE_` variables are missing (frontend will fail)

If any check fails, the script exits with an error and tells you exactly what to fix.

## Best Practices

### 1. Always Use `.env.example` as Template
When cloning or setting up a new environment:
```bash
cp .env.example .env
# Then edit .env with your actual keys
```

### 2. Never Commit `.env` to Git
`.env` is in `.gitignore` for a reason—your API keys are secrets.

### 3. Validate Before Starting
Always run `./setup.sh` instead of directly starting uvicorn. It catches configuration errors early.

### 4. Monitor Health Endpoint in Production
In production, set up monitoring to poll `/health` and alert if status is not "healthy".

### 5. Use Hot Reload for Minor Changes
For simple key rotations, use the `/admin/reload-config` endpoint to avoid downtime.

### 6. Keep a Backup of Working Keys
Before changing keys, note the current working values in case you need to roll back.

## Troubleshooting Flowchart

```
Frontend shows "Failed to fetch"
    ↓
Run: ./test_backend.sh
    ↓
Is server running? → No → Run: ./setup.sh
    ↓ Yes
Check /health output
    ↓
Gemini error? → Check GEMINI_API_KEY in .env, restart or reload
    ↓
Supabase error? → Check SUPABASE_URL and SUPABASE_ANON_KEY, restart or reload
    ↓
All services healthy but frontend still fails?
    ↓
Check VITE_SUPABASE_URL and VITE_SUPABASE_ANON_KEY in .env
    ↓
Restart frontend (Vite dev server) to pick up new env vars
```

## Additional Resources

- [Gemini API Quotas](https://ai.google.dev/gemini-api/docs/rate-limits)
- [Supabase Documentation](https://supabase.com/docs)
- [FastAPI Environment Config](https://fastapi.tiangolo.com/advanced/settings/)

## Need Help?

1. Check the health endpoint: `curl http://localhost:8000/health`
2. Review server logs: `tail -f server.log`
3. Run the test script: `./test_backend.sh`
4. Consult the [README.md](README.md) for API documentation
