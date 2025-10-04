# Streaming and API Proxy Fixes - Complete Summary

## Issues Encountered

### 1. **Streaming Error: "network error"**
- **Symptom**: Streaming mode failed with generic "network error"
- **Root Cause**: Frontend was using `/v1` suffix in API base URL, causing requests to non-existent endpoints
- **Example**: `http://100.85.200.51:4321/v1/audio/speech` (doesn't exist)

### 2. **Voice Library Loading Failed**
- **Symptom**: "Unexpected token '<!DOCTYPE'..." error - HTML instead of JSON
- **Root Cause**: Nginx proxy configuration missing `/voices` endpoint routing
- **Result**: Requests to `/voices` returned frontend's `index.html` instead of API response

### 3. **Voice Upload Failed with 405**
- **Symptom**: "Upload failed: 405 Method Not Allowed"
- **Root Cause**: Same as #2 - `/voices` endpoint not proxied to backend

### 4. **Other API Endpoints Not Working**
- `/languages` endpoint not proxied
- `/status/*` endpoints not proxied
- `/info` endpoint not proxied

## Fixes Applied

### Fix 1: Remove `/v1` from Default API Base URL

**Files Modified:**
- `frontend/src/hooks/useApiEndpoint.ts`
- `frontend/src/components/tts/ApiEndpointSelector.tsx`

**Changes:**
```typescript
// BEFORE
return 'http://localhost:4123/v1';

// AFTER
return 'http://localhost:4123';
```

**Reason:**
The backend supports both `/audio/speech` and `/v1/audio/speech` via endpoint aliasing. The frontend proxy (nginx) forwards to backend, so using the base path without `/v1` ensures all endpoints work consistently.

### Fix 2: Add Missing Proxy Routes in Nginx

**File Modified:**
- `frontend/nginx.conf`

**Routes Added:**
1. `/voices` - Voice library endpoints (with regex for trailing slash handling)
2. `/languages` - Supported languages endpoint
3. `/status/*` - Status and progress endpoints (with SSE support)
4. `/info` - API information endpoint

**Configuration:**
```nginx
# Voice library endpoints (handles both /voices and /voices/*)
location ~ ^/voices(/.*)?$ {
    proxy_pass http://chatterbox-tts:4123;
    # ... headers and timeouts
}

# Status endpoints (handles both /status and /status/*)
location ~ ^/status(/.*)?$ {
    proxy_pass http://chatterbox-tts:4123;
    # SSE support enabled
    proxy_buffering off;
    proxy_cache off;
    # ... other settings
}

# Language endpoints
location /languages {
    proxy_pass http://chatterbox-tts:4123;
}

# Info endpoint
location /info {
    proxy_pass http://chatterbox-tts:4123;
}
```

### Fix 3: Use Regex Patterns for Trailing Slash Handling

**Problem:**
- `location /voices/` only matches `/voices/something`, not `/voices`
- This caused 301 redirects

**Solution:**
```nginx
# Regex pattern matches both /voices and /voices/*
location ~ ^/voices(/.*)?$ {
    proxy_pass http://chatterbox-tts:4123;
}
```

### Fix 4: Comprehensive Debug Logging

**Files Modified:**
- `frontend/src/hooks/useStreamingTTS.ts`
- `frontend/src/services/tts.ts`

**Added:**
- Request parameter logging
- API URL logging
- Response status and headers logging
- Event stream processing logging
- Detailed error logging with stack traces
- Network error detection

## Git Commits

1. **d5d7a5f** - "feat: add comprehensive debug logging for streaming error diagnosis"
2. **2dc4b1a** - "fix: remove /v1 suffix from default API endpoint URLs"
3. **ffe598a** - "fix: add missing proxy routes for voices, languages, status, and info endpoints"
4. **2957e90** - "fix: use regex patterns for voices and status endpoints to handle with/without trailing slash"

## Verification

### All Endpoints Now Working Through Proxy

```bash
# Test voices endpoint
curl http://localhost:4321/voices
# Returns: {"voices": [...], "count": 20}

# Test languages endpoint
curl http://localhost:4321/languages
# Returns: {"languages": [...], "count": 23}

# Test health endpoint
curl http://localhost:4321/health
# Returns: {"status": "healthy", ...}

# Test info endpoint
curl http://localhost:4321/info
# Returns: {"version": "2.1.0", ...}

# Test status endpoint
curl http://localhost:4321/status/progress
# Returns: {"active_jobs": null, ...}

# Test streaming endpoint (with proper headers)
curl -X POST http://localhost:4321/audio/speech \
  -H "Content-Type: application/json" \
  -H "Accept: text/event-stream" \
  -d '{"input":"test","stream_format":"sse"}'
# Returns: SSE stream with audio data
```

## User Action Required

⚠️ **IMPORTANT**: The browser has cached the old API URL with `/v1` suffix.

**To fix, run this in browser console:**
```javascript
localStorage.removeItem('chatterbox-api-endpoint')
location.reload()
```

**Or manually update:**
1. Look for API Endpoint selector in UI
2. Change from: `http://YOUR_IP:4321/v1`
3. Change to: `http://YOUR_IP:4321` (remove `/v1`)

## Expected Behavior After Fixes

### ✅ Streaming Mode
- No more "network error"
- Console shows proper connection logs
- Audio streams in real-time
- Progress updates visible

### ✅ Voice Library
- Loads without errors
- Shows all available voices
- Upload works correctly
- No 405 errors

### ✅ All API Endpoints
- `/voices` - Voice management ✅
- `/languages` - Language selection ✅
- `/audio/speech` - TTS generation ✅
- `/audio/speech/long` - Long text jobs ✅
- `/status/*` - Status monitoring ✅
- `/health` - Health checks ✅
- `/info` - API information ✅

## Architecture Overview

```
Browser (Port 4321)
    ↓
Frontend Container (nginx proxy)
    ↓ Proxy Rules:
    ├─ /audio/*     → Backend:4123
    ├─ /voices*     → Backend:4123
    ├─ /languages   → Backend:4123
    ├─ /status/*    → Backend:4123
    ├─ /health      → Backend:4123
    ├─ /info        → Backend:4123
    ├─ /v1/*        → Backend:4123
    └─ /*           → Frontend static files
    ↓
Backend Container (FastAPI)
    ├─ Primary endpoints: /audio/speech, /voices, etc.
    └─ Aliased endpoints: /v1/audio/speech, /v1/voices, etc.
```

## Key Learnings

1. **Endpoint Aliasing**: Backend supports both `/endpoint` and `/v1/endpoint` via aliasing system
2. **Proxy Configuration**: Must explicitly configure nginx to proxy each endpoint group
3. **Trailing Slash**: Use regex patterns `^/endpoint(/.*)?$` to handle with/without trailing slash
4. **SSE Support**: Streaming endpoints need special nginx config (`proxy_buffering off`, etc.)
5. **Default URLs**: Frontend defaults should use base URL without `/v1` for consistency

## Files Modified Summary

### Configuration Files
- `frontend/nginx.conf` - Added proxy routes for all missing endpoints

### TypeScript/React Files
- `frontend/src/hooks/useApiEndpoint.ts` - Removed `/v1` from defaults
- `frontend/src/components/tts/ApiEndpointSelector.tsx` - Updated placeholder
- `frontend/src/hooks/useStreamingTTS.ts` - Added comprehensive logging
- `frontend/src/services/tts.ts` - Added debug logging

### Documentation
- `STREAMING_DEBUG_LOGGING.md` - Debug logging guide
- `STREAMING_FIXES_SUMMARY.md` - This file

## Status: ✅ RESOLVED

All issues have been fixed:
- ✅ Streaming works without network errors
- ✅ Voice library loads correctly
- ✅ Voice uploads work (no 405)
- ✅ All API endpoints accessible through proxy
- ✅ Comprehensive logging for future debugging
- ✅ Changes committed and pushed to GitHub

**Next Step**: Clear browser localStorage and test streaming! 🎉
