# Long Text Streaming Analysis & Design Documentation

## Overview

This document explains how the long text TTS mode (for texts > 3000 characters) is designed to work and identifies why progressive audio streaming is not functioning as expected.

## System Design

### Architecture Overview

The system has two distinct processing modes:

1. **Standard/Streaming Mode** (≤ 3000 characters)
   - Direct streaming via SSE or audio streaming
   - Real-time audio generation and playback
   - Single request-response model

2. **Long Text Mode** (> 3000 characters)
   - Background job processing
   - Chunk-based generation
   - SSE-based progress updates
   - Designed for progressive playback

### The 3000 Character Threshold

**Location:** Multiple files enforce this threshold:
- `app/models/long_text.py:31` - Backend validation (min_length=3001)
- `frontend/src/hooks/useProcessingMode.ts:77` - Frontend decision logic
- `app/api/endpoints/speech.py:843,1066` - Form validation (max_length=3000)

**Decision Logic:**
```typescript
// Frontend: useProcessingMode.ts
const useLongText = textLength > 3000;
```

```python
# Backend: LongTextRequest model
input: str = Field(..., min_length=3001, description="Text to convert to speech (must be > 3000 characters)")
```

## Long Text Mode Workflow

### Backend Processing Flow

#### 1. Job Creation (`app/api/endpoints/long_text.py:41-117`)
```
POST /audio/speech/long
├── Validate input (> 3000 chars)
├── Create job with unique ID
├── Store metadata and input text
├── Submit to background processor
└── Return job_id and SSE URL
```

#### 2. Background Processing (`app/core/background_tasks.py:122-300`)
```
Background Worker:
├── Phase 1: Text Chunking (CHUNKING status)
│   ├── Uses streaming-optimized chunking if parameters provided
│   ├── Falls back to traditional chunking (Config.LONG_TEXT_CHUNK_SIZE)
│   └── Creates LongTextChunk objects with metadata
│
├── Phase 2: Sequential Audio Generation (PROCESSING status)
│   ├── For each chunk (sequentially):
│   │   ├── Update current_chunk in metadata
│   │   ├── Generate audio via generate_speech_internal()
│   │   ├── Save chunk audio to disk (chunk_XXX.wav)
│   │   ├── Update chunk metadata with audio_file path
│   │   ├── Increment completed_chunks counter
│   │   └── Save updated metadata and chunks data
│   └── Continue even if some chunks fail
│
├── Phase 3: Audio Concatenation (PROCESSING status)
│   ├── Combine all successful chunks
│   ├── Add silence padding between chunks
│   ├── Save final audio file
│   └── Mark job as COMPLETED
```

#### 3. Progress Monitoring (`app/api/endpoints/long_text.py:605-743`)
```
GET /audio/speech/long/{job_id}/sse (SSE Endpoint)
├── Poll loop (every 2 seconds):
│   ├── Load job metadata
│   ├── Load chunks data
│   ├── Check for newly completed chunks
│   ├── For each new completed chunk:
│   │   └── Send chunk_ready event with chunk_url
│   ├── Send progress events (every 5% progress)
│   └── Exit when job is completed/failed/cancelled
```

**Key SSE Events:**
- `chunk_ready` - Sent when a chunk audio file is available
- `progress` - Job progress updates
- `completed` - Job finished successfully
- `error` - Job failed

#### 4. Chunk Download (`app/api/endpoints/long_text.py:285-371`)
```
GET /audio/speech/long/{job_id}/chunks/{chunk_index}
└── Returns individual chunk audio file (WAV)
```

### Frontend Processing Flow

#### 1. Job Submission (`frontend/src/hooks/useLongTextTTS.ts:96-115`)
```typescript
submitJob() → 
├── Call POST /audio/speech/long
├── Receive job_id and sse_url
├── Track job_id in localStorage
└── Start SSE monitoring via startJobMonitoring()
```

#### 2. SSE Event Handling (`frontend/src/services/longTextTTS.ts:209-311`)
```typescript
subscribeToSSE() →
├── Create EventSource connection
├── Listen for events:
│   ├── 'progress' → Update progress state
│   ├── 'chunk_ready' → Download and queue chunk for playback
│   ├── 'completed' → Download final audio
│   └── 'error' → Display error
└── Return cleanup function
```

#### 3. Progressive Chunk Playback (`frontend/src/hooks/useLongTextTTS.ts:248-329`)
```typescript
Chunk Playback Queue System:
├── playChunk(chunkIndex, chunkUrl)
│   ├── Fetch chunk audio blob
│   ├── Create object URL
│   ├── Add to chunkQueueRef
│   └── Start playback if not already playing
│
└── playNextChunk() (Sequential Player)
    ├── Check if queue has chunks
    ├── Check if currently playing
    ├── Take next chunk from queue
    ├── Create Audio element
    ├── Play audio
    └── On ended: Play next chunk
```

## The Streaming Problem

### Expected Behavior

1. User submits text > 3000 characters
2. Backend starts processing chunks sequentially
3. As EACH chunk completes:
   - Chunk audio file is saved to disk
   - SSE `chunk_ready` event is sent immediately
   - Frontend receives event, downloads chunk, plays it
4. User hears audio starting within seconds, with continuous playback as chunks arrive

### Actual Behavior

1. User submits text > 3000 characters
2. Backend processes ALL chunks sequentially
3. Chunks complete but audio doesn't start playing immediately
4. Frontend receives chunk events but playback is delayed or doesn't start in real-time

### Root Causes Identified

#### 1. **SSE Polling Delay** (Major Issue)
**Location:** `app/api/endpoints/long_text.py:712`

```python
# Wait before next check
await asyncio.sleep(2)
```

**Impact:** 
- SSE endpoint polls for completed chunks every 2 seconds
- This introduces 0-2 second delay for each chunk notification
- Delays accumulate across multiple chunks
- Not true "real-time" streaming

**Why This Matters:**
- Chunk generation is sequential (chunk 2 starts after chunk 1 finishes)
- Each chunk takes several seconds to generate
- The 2-second polling delay adds unnecessary latency on top of generation time
- First chunk might be ready in 5 seconds, but frontend doesn't know for 0-7 seconds (5 + polling delay)

#### 2. **No Event-Driven Notification** (Architectural Issue)
**Location:** `app/core/background_tasks.py:246-251`

```python
# Update job progress
current_metadata.completed_chunks = i + 1
self.job_manager._save_job_metadata(current_metadata)
self.job_manager._save_chunks_data(job_id, chunks)

logger.info(f"Job {job_id}: Completed chunk {i+1}/{len(chunks)}")
```

**Problem:**
- Chunks are saved to disk
- Metadata is updated
- **But NO SSE event is emitted here**
- SSE endpoint discovers chunks only through polling

**Better Design Would Be:**
- Background processor emits event when chunk completes
- SSE endpoint forwards event immediately to connected clients
- Zero polling delay

#### 3. **Frontend Service Configuration** (Bypass Mechanism)
**Location:** `frontend/src/services/longTextTTS.ts:326`

```typescript
shouldUseLongText: (text: string): boolean => {
  return text.length > 999999; // Bypass long text - always use streaming
},
```

**Analysis:**
- This function is defined but **NOT USED** in the main flow
- Frontend uses `shouldUseLongTextManual` from `useProcessingMode` hook instead
- The comment suggests intentional bypass at some point in development
- Current threshold check is at 3000 chars via `useProcessingMode.ts`

**Status:** Not the root cause, but indicates historical issues with long text mode

#### 4. **Sequential Chunk Processing** (Design Limitation)
**Location:** `app/core/background_tasks.py:203-264`

```python
for i, chunk in enumerate(chunks):
    # Generate audio for this chunk
    audio_buffer = await generate_speech_internal(...)
```

**Impact:**
- Chunks are processed one at a time (sequential)
- Chunk N+1 can't start until chunk N completes
- This is necessary for final concatenation but limits parallelism
- For a 10-chunk job:
  - Chunk 1: Available at 5s
  - Chunk 2: Available at 10s
  - Chunk 3: Available at 15s
  - etc.

**Why Sequential:**
- Maintains chunk order for final concatenation
- Memory management (avoid loading all chunks simultaneously)
- VRAM constraints when using GPU

### Why It Doesn't Stream in Real-Time

**Timeline Example** (10,000 character text = ~4 chunks):

```
Expected Timeline (Ideal):
0s:   Job submitted
5s:   Chunk 0 ready → Frontend starts playing
10s:  Chunk 1 ready → Queued (Chunk 0 still playing)
15s:  Chunk 2 ready → Queued
20s:  Chunk 3 ready → Queued
25s:  All chunks played, final audio available

Actual Timeline (Current):
0s:   Job submitted
5s:   Chunk 0 ready (saved to disk)
7s:   SSE polls and detects chunk 0 → Frontend downloads → Playback MAY start
10s:  Chunk 1 ready (saved to disk)
12s:  SSE polls and detects chunk 1 → Frontend downloads
15s:  Chunk 2 ready (saved to disk)
17s:  SSE polls and detects chunk 2 → Frontend downloads
20s:  Chunk 3 ready (saved to disk)
22s:  SSE polls and detects chunk 3 → Frontend downloads
30s:  Final concatenation complete

Total Delay: ~7 seconds from first chunk ready to first audio playback
           + 2-second delays for each subsequent chunk
```

## Comparison: Streaming Mode vs Long Text Mode

### Standard Streaming Mode (≤3000 chars)
**Endpoint:** `POST /audio/speech` with streaming enabled

```
Request → 
├── Text chunking (immediate)
├── Generate chunk 1 → Yield audio bytes → Frontend plays
├── Generate chunk 2 → Yield audio bytes → Frontend plays
└── Generate chunk 3 → Yield audio bytes → Frontend plays

Timeline:
- First audio bytes: ~1-2 seconds
- Continuous streaming
- No polling delay
```

### Long Text Mode (>3000 chars)  
**Endpoint:** `POST /audio/speech/long`

```
Request →
├── Create job (background)
├── Generate ALL chunks sequentially
├── Poll for completed chunks (every 2s)
└── Download and play chunks

Timeline:
- First audio playback: ~5-7 seconds (or more)
- Polling delays between chunks
- Not truly "streaming"
```

## Why Progressive Playback Was Designed But Doesn't Work Well

### Design Intent (from code analysis):

1. **Progressive Streaming Support:**
   - `chunk_ready` SSE events (line 646 in long_text.py)
   - Chunk download endpoint (line 285 in long_text.py)
   - Frontend playback queue (line 55 in useLongTextTTS.ts)
   - Sequential audio player (line 248 in useLongTextTTS.ts)

2. **Smart Features:**
   - Chunks saved individually for progressive access
   - Queue management to play chunks in order
   - Audio element with automatic next-chunk trigger
   - Blob URL cleanup

### Why It Falls Short:

1. **Polling Overhead:** 2-second intervals too slow for responsive streaming
2. **No Push Notifications:** Backend doesn't push events when chunks complete
3. **Sequential Generation:** Can't parallelize chunk generation
4. **Network Latency:** Each chunk requires separate HTTP request
5. **Browser Autoplay:** May require user interaction for audio playback

## Recommendations

### Immediate Fixes (Quick Wins)

#### 1. Reduce SSE Polling Interval
**File:** `app/api/endpoints/long_text.py:712`

```python
# CURRENT
await asyncio.sleep(2)

# RECOMMENDED
await asyncio.sleep(0.5)  # Check every 500ms
```

**Impact:** 4x reduction in notification latency

#### 2. Add Immediate Notification on Chunk Completion
**File:** `app/core/background_tasks.py:251`

```python
# After saving chunk data
self.job_manager._save_chunks_data(job_id, chunks)

# ADD: Trigger immediate SSE notification
await self.job_manager.notify_chunk_ready(job_id, i, chunk_filename)
```

**Impact:** Near-instant notification (< 100ms)

### Medium-Term Improvements

#### 3. Event-Driven SSE Architecture
**Approach:**
- Use asyncio.Queue for event distribution
- Background processor puts events in queue
- SSE endpoint consumes from queue
- No polling needed

**Implementation:**
```python
class LongTextJobManager:
    def __init__(self):
        self.event_queues: Dict[str, asyncio.Queue] = {}
    
    async def emit_event(self, job_id: str, event: LongTextSSEEvent):
        if job_id in self.event_queues:
            await self.event_queues[job_id].put(event)
```

#### 4. Parallel Chunk Generation (Optional)
**Consideration:**
- Generate 2-3 chunks in parallel
- More responsive for first chunk
- Higher memory/VRAM usage
- Needs careful synchronization

### Long-Term Optimizations

#### 5. WebSocket-Based Streaming
**Benefits:**
- True bidirectional communication
- Lower latency than SSE
- Better error handling

#### 6. Hybrid Approach
**For texts 3000-10000 chars:**
- Use enhanced streaming mode instead
- Generate larger chunks
- Stream directly without job queue

**For texts >10000 chars:**
- Use long text job mode
- Implement event-driven notifications

## Configuration & Settings

### Current Thresholds
```python
# app/config.py
LONG_TEXT_CHUNK_SIZE = 500  # Characters per chunk
LONG_TEXT_MAX_LENGTH = 100000  # Maximum text length
LONG_TEXT_SILENCE_PADDING_MS = 200  # Silence between chunks
```

### Frontend Threshold
```typescript
// frontend/src/hooks/useProcessingMode.ts
const useLongText = textLength > 3000;
```

## Testing Progressive Playback

### Test Case 1: Verify SSE Events
```bash
# Monitor SSE stream
curl -N http://localhost:8000/audio/speech/long/{job_id}/sse
```

**Expected:** `chunk_ready` events appear within 500ms of chunk completion

### Test Case 2: Verify Chunk Downloads
```bash
# Download specific chunk
curl http://localhost:8000/audio/speech/long/{job_id}/chunks/0 -o chunk0.wav
```

### Test Case 3: Frontend Playback
```javascript
// Browser console
console.log('[AudioQueue] Queue status:', chunkQueueRef.current);
console.log('[AudioQueue] Currently playing:', isPlayingRef.current);
```

**Expected:** Chunks queue up and play sequentially

## Conclusion

The long text streaming system has all the necessary components for progressive audio playback:
- Chunk-based processing ✓
- Progressive chunk download endpoint ✓
- SSE event infrastructure ✓
- Frontend playback queue ✓

**However**, the implementation has a critical flaw:
- **SSE polling with 2-second intervals** creates unacceptable latency
- **No event-driven notification** from background processor
- Results in 5-7+ second delay before audio starts playing
- Not a true "streaming" experience for the user

**Quick Fix:** Reduce polling interval to 500ms (4x faster)

**Proper Fix:** Implement event-driven SSE with immediate notifications when chunks complete

**User Experience Goal:** First audio playback within 2-3 seconds of job submission, with continuous playback as chunks arrive.

---

*Generated: 2025-10-05*
*Project: Chatterbox TTS API*
