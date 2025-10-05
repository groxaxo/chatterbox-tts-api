# Long Text TTS Flow Diagram

## System Overview

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         TEXT INPUT (Frontend)                            │
│                                                                          │
│  User enters text and clicks "Generate Speech"                          │
└────────────────────────────────┬────────────────────────────────────────┘
                                 │
                    ┌────────────▼────────────┐
                    │  Text Length Check      │
                    │  (useProcessingMode)    │
                    └────────────┬────────────┘
                                 │
                ┌────────────────┴────────────────┐
                │                                 │
     ┌──────────▼─────────┐          ┌──────────▼──────────┐
     │  ≤ 3000 chars      │          │  > 3000 chars       │
     │  STREAMING MODE    │          │  LONG TEXT MODE     │
     └──────────┬─────────┘          └──────────┬──────────┘
                │                               │
                │                               │
                └───────────────┬───────────────┘
                                │
                                ▼
```

## Streaming Mode Flow (≤ 3000 chars)

```
Frontend                          Backend
   │                                 │
   │  POST /audio/speech             │
   │  (with streaming enabled)       │
   ├────────────────────────────────►│
   │                                 │
   │                                 │ Split text into chunks
   │                                 │ Generate chunk 1
   │                                 ├──► Yield audio bytes
   │◄────────────────────────────────┤
   │ Start playing immediately       │
   │                                 │ Generate chunk 2
   │                                 ├──► Yield audio bytes
   │◄────────────────────────────────┤
   │ Continuous playback             │
   │                                 │ Generate chunk 3
   │                                 ├──► Yield audio bytes
   │◄────────────────────────────────┤
   │                                 │
   │                                 │ Complete
   ▼                                 ▼

Timeline: First audio in ~1-2 seconds
```

## Long Text Mode Flow (> 3000 chars) - CURRENT IMPLEMENTATION

```
Frontend                          Backend                     Background Processor
   │                                 │                              │
   │  POST /audio/speech/long        │                              │
   ├────────────────────────────────►│                              │
   │                                 │  Create job                  │
   │                                 │  Return job_id               │
   │◄────────────────────────────────┤                              │
   │                                 │                              │
   │  GET /sse (EventSource)         │  Submit to queue             │
   ├────────────────────────────────►├─────────────────────────────►│
   │                                 │                              │
   │                                 │                              │ Process job:
   │                                 │                              │ ├─ Split text
   │                                 │                              │ ├─ Generate chunk 0
   │                                 │                              │ ├─ Save to disk ✓
   │      ⏰ 2 second delay           │                              │
   │                                 │  Poll: Any new chunks?       │
   │                                 │◄─────────────────────────────┤
   │                                 │  Yes! chunk 0 ready          │
   │  SSE: chunk_ready event         │                              │
   │◄────────────────────────────────┤                              │
   │  Download chunk 0               │                              │
   ├────────────────────────────────►│                              │
   │◄────────────────────────────────┤                              │
   │  🔊 Start playing chunk 0       │                              │
   │                                 │                              │
   │                                 │                              │ Generate chunk 1
   │                                 │                              │ Save to disk ✓
   │      ⏰ 2 second delay           │                              │
   │                                 │  Poll: Any new chunks?       │
   │                                 │◄─────────────────────────────┤
   │  SSE: chunk_ready event         │                              │
   │◄────────────────────────────────┤                              │
   │  Download chunk 1               │                              │
   │  Queue for playback             │                              │
   │                                 │                              │
   │                                 │                              │ Generate chunk 2
   │                                 │                              │ Save to disk ✓
   │      ⏰ 2 second delay           │                              │
   │                                 │  Poll: Any new chunks?       │
   │                                 │◄─────────────────────────────┤
   │  SSE: chunk_ready event         │                              │
   │◄────────────────────────────────┤                              │
   │  Download chunk 2               │                              │
   │  Queue for playback             │                              │
   │                                 │                              │
   │                                 │                              │ Concatenate all
   │                                 │                              │ Mark complete ✓
   │                                 │  Poll: Job complete?         │
   │                                 │◄─────────────────────────────┤
   │  SSE: completed event           │                              │
   │◄────────────────────────────────┤                              │
   │  Close SSE connection           │                              │
   ▼                                 ▼                              ▼

Timeline: First audio in ~5-7 seconds (includes 2s polling delay)
Problem: ⏰ Polling every 2 seconds adds latency
```

## The Problem Visualized

```
Chunk Generation Timeline:

Ideal (Event-Driven):
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
0s        5s        10s       15s       20s
├─────────┼─────────┼─────────┼─────────┤
│ Gen C0  │ Gen C1  │ Gen C2  │ Gen C3  │
└─►Play   └─►Queue  └─►Queue  └─►Queue
  Instant   Instant   Instant   Instant
  
  
Current (Polling with 2s delay):
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
0s        5s        10s       15s       20s
├─────────┼─────────┼─────────┼─────────┤
│ Gen C0  │ Gen C1  │ Gen C2  │ Gen C3  │
└──►⏰──►Play       └──►⏰──►Queue
   0-2s delay        0-2s delay
   
   
Proposed (Polling with 0.2s delay):
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
0s        5s        10s       15s       20s
├─────────┼─────────┼─────────┼─────────┤
│ Gen C0  │ Gen C1  │ Gen C2  │ Gen C3  │
└►⏰►Play   └►⏰►Queue  └►⏰►Queue
  0.2s      0.2s      0.2s
```

## Frontend Chunk Playback Queue

```
┌──────────────────────────────────────────────────┐
│         useLongTextTTS.ts                        │
│                                                  │
│  ┌────────────────────────────────────────┐     │
│  │  chunkQueueRef                         │     │
│  │  [chunk0, chunk1, chunk2, ...]         │     │
│  └──────────┬─────────────────────────────┘     │
│             │                                    │
│             ▼                                    │
│  ┌────────────────────────────────────────┐     │
│  │  playNextChunk()                       │     │
│  │  ├─ Take first chunk from queue        │     │
│  │  ├─ Create Audio element               │     │
│  │  ├─ Play audio                         │     │
│  │  └─ onended: playNextChunk()           │     │
│  └────────────────────────────────────────┘     │
│             │                                    │
│             ▼                                    │
│  ┌────────────────────────────────────────┐     │
│  │  Sequential Playback                   │     │
│  │  Chunk 0 ──► Chunk 1 ──► Chunk 2       │     │
│  └────────────────────────────────────────┘     │
└──────────────────────────────────────────────────┘

Frontend is READY for streaming!
Problem is ONLY backend notification speed.
```

## SSE Event Flow (Current)

```
Background Processor                SSE Endpoint              Frontend
       │                                 │                       │
       │ Generate chunk 0                │                       │
       │ Save to disk                    │                       │
       │                                 │                       │
       │                     ⏰ Poll timer (2s interval)          │
       │                                 │                       │
       │                                 │ Load metadata         │
       │                                 │ Load chunks           │
       │                                 │ Find: chunk 0 ready!  │
       │                                 │                       │
       │                                 │  chunk_ready event    │
       │                                 ├──────────────────────►│
       │                                 │                       │
       │ Generate chunk 1                │                       │
       │ Save to disk                    │                       │
       │                                 │                       │
       │                     ⏰ Poll timer (2s interval)          │
       │                                 │                       │
       │                                 │ Find: chunk 1 ready!  │
       │                                 │  chunk_ready event    │
       │                                 ├──────────────────────►│
       ▼                                 ▼                       ▼

Delay: 0-2 seconds per chunk (average 1 second)
```

## SSE Event Flow (Proposed: Event-Driven)

```
Background Processor                SSE Endpoint              Frontend
       │                                 │                       │
       │ Generate chunk 0                │                       │
       │ Save to disk                    │                       │
       │ Emit event ─────────────────────►                       │
       │                                 │  chunk_ready event    │
       │                                 ├──────────────────────►│
       │                                 │                       │
       │ Generate chunk 1                │                       │
       │ Save to disk                    │                       │
       │ Emit event ─────────────────────►                       │
       │                                 │  chunk_ready event    │
       │                                 ├──────────────────────►│
       │                                 │                       │
       │ Generate chunk 2                │                       │
       │ Save to disk                    │                       │
       │ Emit event ─────────────────────►                       │
       │                                 │  chunk_ready event    │
       │                                 ├──────────────────────►│
       ▼                                 ▼                       ▼

Delay: < 10ms per chunk (near instant)
```

## File Structure for Long Text Jobs

```
data/long_text_jobs/
└── {job_id}/
    ├── metadata.json          # Job status, progress, parameters
    ├── input_text.txt         # Original input text
    ├── chunks.json            # Chunk metadata (text previews, status)
    ├── chunks/                # Individual chunk audio files
    │   ├── chunk_001.wav
    │   ├── chunk_002.wav
    │   ├── chunk_003.wav
    │   └── chunk_004.wav
    └── output/
        └── final.mp3          # Concatenated final audio

Progressive Streaming Access:
- Frontend downloads: /audio/speech/long/{job_id}/chunks/0
- Frontend downloads: /audio/speech/long/{job_id}/chunks/1
- Frontend downloads: /audio/speech/long/{job_id}/chunks/2
- Final download:     /audio/speech/long/{job_id}/download
```

## Key Components

### Backend Files
- `app/api/endpoints/long_text.py` - REST endpoints and SSE
- `app/core/background_tasks.py` - Chunk generation processor
- `app/core/long_text_jobs.py` - Job management and persistence
- `app/models/long_text.py` - Data models

### Frontend Files  
- `frontend/src/services/longTextTTS.ts` - API service layer
- `frontend/src/hooks/useLongTextTTS.ts` - React hook with playback queue
- `frontend/src/hooks/useProcessingMode.ts` - Mode selection logic
- `frontend/src/pages/TTSPage.tsx` - Main UI integration

## Configuration

```python
# Backend: app/config.py
LONG_TEXT_CHUNK_SIZE = 500              # Characters per chunk
LONG_TEXT_MAX_LENGTH = 100000           # Maximum input length
LONG_TEXT_MAX_CONCURRENT_JOBS = 2       # Parallel job limit
LONG_TEXT_SILENCE_PADDING_MS = 200      # Silence between chunks
```

```typescript
// Frontend: useProcessingMode.ts
threshold: 3000  // Switch to long text mode above this
```

## Summary

✅ **What Works:**
- Chunk generation and storage
- SSE infrastructure
- Frontend playback queue
- Progressive chunk download

❌ **What Doesn't Work:**
- Real-time streaming due to 2-second polling delay
- Results in 5-7+ second delay for first audio

🔧 **Fix:**
- Change `await asyncio.sleep(2)` to `await asyncio.sleep(0.2)` in `app/api/endpoints/long_text.py:712`
- Or implement event-driven notifications for instant updates
