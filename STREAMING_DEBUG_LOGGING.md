# Comprehensive Streaming Debug Logging

## Overview

Added **extensive verbose logging** throughout the entire streaming pipeline to diagnose the "Streaming Error network error" issue.

## Logging Added

### 1. Frontend Hook (`useStreamingTTS.ts`)

#### SSE Streaming Start
```
[StreamingTTS] ===== STARTING SSE STREAMING =====
[StreamingTTS] Request: {input_length, voice, exaggeration, cfg_weight, temperature, streaming_chunk_size, streaming_strategy, streaming_quality}
[StreamingTTS] API Base URL: <url>
[StreamingTTS] Setting state to streaming...
[StreamingTTS] Creating AbortController
[StreamingTTS] Resetting audio context scheduling
[StreamingTTS] Calling ttsService.generateSpeechSSE...
```

#### During Streaming
```
[StreamingTTS] Received SSE event: {type, progress}
[StreamingTTS] Received audio info: <audio_info>
[StreamingTTS] Received audio delta, chunk size: <size>
[StreamingTTS] Total PCM chunks collected: <count>
[StreamingTTS] Received audio.done event
[StreamingTTS] Creating final audio from <n> chunks
[StreamingTTS] Final audio created, URL: <url>
```

#### On Success
```
[StreamingTTS] ===== SSE STREAMING COMPLETED SUCCESSFULLY =====
```

#### On Error
```
[StreamingTTS] ===== SSE STREAMING ERROR =====
[StreamingTTS] Error details: <error>
[StreamingTTS] Error type: <type>
[StreamingTTS] Error message: <message>
[StreamingTTS] Error stack: <stack>
[StreamingTTS] NETWORK ERROR: Failed to fetch from server
[StreamingTTS] Check if backend is running at: <url>
```

### 2. TTS Service (`tts.ts`)

#### Service Call
```
[TTS Service] ===== generateSpeechSSE CALLED =====
[TTS Service] Request data: {input_length, voice, stream_format, streaming_chunk_size, streaming_strategy}
[TTS Service] Fetching from: <url>
[TTS Service] Response status: <status>
[TTS Service] Response ok: <true/false>
[TTS Service] Response headers: <headers>
```

#### Response Errors
```
[TTS Service] Response not OK!
[TTS Service] Status: <status>
[TTS Service] Error text: <error>
```

#### Stream Processing
```
[TTS Service] Starting to read response stream...
[TTS Service] Read <n> chunks so far...
[TTS Service] Stream done, total chunks read: <count>
[TTS Service] Parsed SSE event: <type>
[TTS Service] Audio delta: {chunksReceived, totalBytes, deltaSize}
[TTS Service] Received speech.audio.done, completing stream
```

#### Stream Errors
```
[TTS Service] ===== ERROR IN STREAM READING =====
[TTS Service] Error: <error>
[TTS Service] Error type: <type>
[TTS Service] Error message: <message>
[TTS Service] Error stack: <stack>
```

## Files Modified

1. **`frontend/src/hooks/useStreamingTTS.ts`**
   - Added comprehensive logging to `startSSEStreaming` function
   - Logs request details, API URL, state changes
   - Logs each SSE event received
   - Detailed error logging with network error detection
   - Logs audio chunk processing

2. **`frontend/src/services/tts.ts`**
   - Added logging to `generateSpeechSSE` function
   - Logs fetch request and response details
   - Logs response headers for debugging
   - Logs stream reading progress
   - Logs each parsed SSE event
   - Detailed error logging with stack traces

## How to Use

### Step 1: Open Browser Console
1. Navigate to TTS interface
2. Open Developer Tools (F12)
3. Go to Console tab
4. Clear console for clean view

### Step 2: Trigger Streaming
1. Enter text in the input field
2. Make sure "Streaming" mode is selected (or "Auto" with < 3000 chars)
3. Click "Generate Speech"

### Step 3: Read the Logs

#### If Working Correctly:
You'll see a complete flow like:
```
[StreamingTTS] ===== STARTING SSE STREAMING =====
[StreamingTTS] Request: {...}
[TTS Service] ===== generateSpeechSSE CALLED =====
[TTS Service] Response status: 200
[TTS Service] Response ok: true
[TTS Service] Starting to read response stream...
[TTS Service] Parsed SSE event: speech.audio.info
[StreamingTTS] Received audio info: {...}
[TTS Service] Parsed SSE event: speech.audio.delta
[StreamingTTS] Received audio delta, chunk size: 12345
... (more deltas) ...
[TTS Service] Received speech.audio.done, completing stream
[StreamingTTS] ===== SSE STREAMING COMPLETED SUCCESSFULLY =====
```

#### If Network Error:
You'll see:
```
[StreamingTTS] ===== STARTING SSE STREAMING =====
[TTS Service] ===== generateSpeechSSE CALLED =====
[StreamingTTS] ===== SSE STREAMING ERROR =====
[StreamingTTS] NETWORK ERROR: Failed to fetch from server
[StreamingTTS] Check if backend is running at: <url>
```

**Diagnosis**: Backend not reachable - check:
- Is backend container running?
- Is API base URL correct?
- Network connectivity?

#### If Response Not OK:
```
[TTS Service] Response not OK!
[TTS Service] Status: 500
[TTS Service] Error text: <error details>
```

**Diagnosis**: Backend returned error - check:
- Backend logs for error details
- Request parameters validity
- Backend health status

#### If Stream Fails Mid-Processing:
```
[TTS Service] Starting to read response stream...
[TTS Service] Read 10 chunks so far...
[TTS Service] ===== ERROR IN STREAM READING =====
[TTS Service] Error: <error>
```

**Diagnosis**: Stream interrupted - check:
- Network stability
- Backend processing errors
- Timeout settings

## Common Error Patterns

### Pattern 1: "network error"
```
[StreamingTTS] NETWORK ERROR: Failed to fetch from server
```
**Cause**: Cannot connect to backend  
**Solution**: Verify backend is running and API URL is correct

### Pattern 2: "Response not OK"
```
[TTS Service] Status: 400
[TTS Service] Error text: Invalid request parameters
```
**Cause**: Invalid request  
**Solution**: Check request parameters in logs

### Pattern 3: "Response body is null"
```
[TTS Service] Response body is null!
```
**Cause**: Empty response from backend  
**Solution**: Check backend streaming implementation

### Pattern 4: "Audio info not received"
```
[StreamingTTS] No audio info received!
```
**Cause**: Missing speech.audio.info event  
**Solution**: Backend not sending audio info event

### Pattern 5: Stream timeout
```
[TTS Service] Read 10 chunks so far...
<no more logs>
```
**Cause**: Stream stalled  
**Solution**: Check backend for processing delays

## Backend Logging

To get complete visibility, also check backend logs:

```bash
docker logs chatterbox-tts-api-gpu --tail 100 -f
```

Look for:
- Request received
- TTS generation started
- Streaming events sent
- Any errors or exceptions

## Next Steps for Debugging

1. **Capture console output** - Copy all [StreamingTTS] and [TTS Service] logs
2. **Check backend logs** - Look for corresponding backend errors
3. **Verify API endpoint** - Ensure correct URL is being used
4. **Test with curl** - Try streaming endpoint directly:
   ```bash
   curl -X POST http://localhost:4123/audio/speech \
     -H "Content-Type: application/json" \
     -H "Accept: text/event-stream" \
     -d '{"input":"test","stream_format":"sse"}'
   ```

5. **Check network tab** - In DevTools, check Network tab for:
   - Request URL
   - Request headers
   - Request payload
   - Response status
   - Response headers

## Error Resolution Flow

```
Network Error?
├── Yes → Check backend status, API URL
└── No → Check response status
    ├── Not 200 → Check request parameters, backend logs
    └── 200 → Check stream processing
        ├── No events → Backend not sending events
        └── Events stop → Stream interrupted, check logs
```

## Conclusion

With this extensive logging, you can now pinpoint exactly where the streaming process fails. Every step from request initiation to final audio creation is logged, making debugging much easier.

**Share the console logs to diagnose your specific "network error" issue!**
