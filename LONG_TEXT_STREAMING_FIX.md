# Quick Fix Guide: Long Text Streaming Issue

## Problem Summary

When text exceeds 3000 characters, the system switches to "long text mode" which processes audio in chunks. While the backend generates chunks successfully, the frontend doesn't start playing audio in real-time because:

1. **SSE polling is too slow** - Checks every 2 seconds instead of immediately notifying
2. **No event-driven notifications** - Backend doesn't push events when chunks complete
3. Results in **5-7+ second delay** before first audio plays

## The Root Cause

**Location:** `app/api/endpoints/long_text.py:712`

```python
# Wait before next check
await asyncio.sleep(2)  # ← THIS IS THE PROBLEM
```

The SSE endpoint polls for completed chunks every 2 seconds. Combined with chunk generation time, this creates significant delays.

## Quick Fix Options

### Option 1: Reduce Polling Interval (Easiest)

**Estimated Time:** 2 minutes  
**Impact:** 4x faster notification  
**Risk:** Very low

**Change:** `app/api/endpoints/long_text.py:712`

```python
# BEFORE
await asyncio.sleep(2)

# AFTER
await asyncio.sleep(0.5)  # Check every 500ms
```

**Result:** Chunks detected 4x faster (500ms vs 2000ms average delay)

### Option 2: Even More Aggressive Polling (Moderate Resource Use)

**Estimated Time:** 2 minutes  
**Impact:** 10x faster notification  
**Risk:** Low (slightly higher CPU)

```python
# AFTER
await asyncio.sleep(0.2)  # Check every 200ms
```

**Result:** Near-instant detection (< 200ms delay)

### Option 3: Event-Driven Architecture (Best, But More Work)

**Estimated Time:** 30-60 minutes  
**Impact:** Instant notification (< 10ms)  
**Risk:** Medium (requires architectural changes)

This requires:
1. Adding event queue to JobManager
2. Emitting events when chunks complete
3. SSE endpoint consuming from event queue instead of polling

See `LONG_TEXT_STREAMING_ANALYSIS.md` for detailed implementation.

## Recommended Immediate Action

**Apply Option 1 or 2:**

1. Open `app/api/endpoints/long_text.py`
2. Find line 712: `await asyncio.sleep(2)`
3. Change to: `await asyncio.sleep(0.5)` or `await asyncio.sleep(0.2)`
4. Restart the server
5. Test with text > 3000 characters

## Expected Improvement

### Before Fix:
```
Timeline for 10,000 character text (4 chunks):
0s:   Submit job
5s:   Chunk 0 ready
7s:   Frontend notified (2s polling delay) → Download → Play
10s:  Chunk 1 ready
12s:  Frontend notified → Download
15s:  Chunk 2 ready
17s:  Frontend notified → Download
20s:  Chunk 3 ready
22s:  Frontend notified → Download

First audio: 7 seconds after submission
```

### After Fix (0.5s polling):
```
Timeline for 10,000 character text (4 chunks):
0s:   Submit job
5s:   Chunk 0 ready
5.5s: Frontend notified (0.5s polling delay) → Download → Play
10s:  Chunk 1 ready
10.5s: Frontend notified → Download
15s:  Chunk 2 ready
15.5s: Frontend notified → Download
20s:  Chunk 3 ready
20.5s: Frontend notified → Download

First audio: 5.5 seconds after submission (1.5s improvement)
```

### After Fix (0.2s polling):
```
Timeline for 10,000 character text (4 chunks):
0s:   Submit job
5s:   Chunk 0 ready
5.2s: Frontend notified (0.2s polling delay) → Download → Play
10s:  Chunk 1 ready
10.2s: Frontend notified → Download
15s:  Chunk 2 ready
15.2s: Frontend notified → Download
20s:  Chunk 3 ready
20.2s: Frontend notified → Download

First audio: 5.2 seconds after submission (1.8s improvement)
```

## Testing

1. Start the server with the fix
2. Enter text > 3000 characters in the frontend
3. Click "Generate Speech"
4. Observe console logs for:
   ```
   [Long Text TTS] Received SSE event for job ...: chunk_ready
   [Chunk Download] ⬇️  Downloading chunk 0
   [AudioQueue] 🔊 Playing chunk 0
   ```
5. Audio should start playing within 5-6 seconds (vs 7-10 seconds before)

## Additional Notes

### Why Not Even Faster Polling?

- **0.5s-0.2s is optimal balance** between responsiveness and resource usage
- Polling every 50ms would work but uses unnecessary CPU
- Event-driven approach (Option 3) is better for < 100ms latency

### Browser Autoplay Policy

The frontend might still face browser autoplay restrictions:
```
[AudioQueue] ❌ Failed to play chunk. This might be due to browser autoplay policy.
```

**Solution:** User must interact with the page before audio can play automatically. This is a browser security feature, not a bug.

### Frontend Already Has Playback Queue

The frontend code in `useLongTextTTS.ts` already implements:
- ✓ Chunk download queue
- ✓ Sequential playback
- ✓ Automatic next-chunk trigger
- ✓ Error handling

The ONLY issue is backend notification speed.

## Files Involved

- **Backend SSE Endpoint:** `app/api/endpoints/long_text.py:605-743`
- **Background Processor:** `app/core/background_tasks.py:122-300`
- **Frontend SSE Handler:** `frontend/src/services/longTextTTS.ts:209-311`
- **Frontend Playback:** `frontend/src/hooks/useLongTextTTS.ts:248-329`

## Related Documentation

- Full analysis: `LONG_TEXT_STREAMING_ANALYSIS.md`
- Architecture decisions in commit history
- Frontend queue implementation comments

---

**Status:** Ready to implement  
**Priority:** High (user-facing feature not working as designed)  
**Effort:** 2 minutes for quick fix, 1 hour for proper fix
