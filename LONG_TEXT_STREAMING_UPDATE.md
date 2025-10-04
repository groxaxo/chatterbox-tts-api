# Long Text Streaming Update

## Summary

Successfully updated the long text processing to use **exactly the same streaming-optimized chunking** as standard streaming generations. This ensures consistent behavior across both processing modes.

## Changes Made

### Backend Changes

#### 1. **LongTextRequest Model** (`app/models/long_text.py`)
- Added streaming parameters to match standard streaming:
  - `streaming_chunk_size` (optional): Target chunk size
  - `streaming_strategy` (optional): Chunking strategy (sentence, paragraph, word, fixed)
  - `streaming_quality` (optional): Quality preset (fast, balanced, high)

#### 2. **Job Manager** (`app/core/long_text_jobs.py`)
- Updated `create_job()` to accept streaming parameters
- Store streaming settings in job metadata for processing

#### 3. **Background Processor** (`app/core/background_tasks.py`)
- Modified text chunking logic to use streaming-optimized chunking when parameters are provided
- Falls back to traditional long text chunking if no streaming parameters specified
- Uses `split_text_for_streaming()` and `get_streaming_settings()` from text_processing module
- Converts streaming text chunks to `LongTextChunk` objects for job tracking

#### 4. **API Endpoint** (`app/api/endpoints/long_text.py`)
- Pass streaming parameters from request to job creation

### Frontend Changes

#### 1. **Type Definitions** (`frontend/src/types/index.ts`)
- Added streaming parameters to `LongTextRequest` interface

#### 2. **Service Layer** (`frontend/src/services/longTextTTS.ts`)
- Updated `submitJob()` to send streaming parameters in request payload

#### 3. **Advanced Settings Hook** (`frontend/src/hooks/useAdvancedSettings.ts`)
- Extended settings to include:
  - `streamingChunkSize`
  - `streamingStrategy` (default: 'sentence')
  - `streamingQuality` (default: 'balanced')
- Added update functions for streaming settings
- Persist streaming settings in localStorage

#### 4. **TTS Page** (`frontend/src/pages/TTSPage.tsx`)
- Extract streaming settings from advanced settings hook
- Pass streaming parameters to long text job submission

## How It Works

### Standard Streaming
1. User inputs text < 3000 chars
2. Text is chunked using `split_text_for_streaming()` with streaming parameters
3. Each chunk is processed and streamed to the client in real-time

### Long Text Processing (Now Updated)
1. User inputs text > 3000 chars
2. Job is created with **same streaming parameters**
3. Text is chunked using `split_text_for_streaming()` (same function as streaming)
4. Each chunk is processed sequentially
5. Chunks are concatenated into final audio
6. Progressive streaming available via SSE for completed chunks

## Benefits

1. **Consistency**: Both processing modes use identical chunking logic
2. **Quality**: Long text jobs benefit from streaming-optimized sentence/paragraph boundaries
3. **User Control**: Users can configure chunking strategy for long text
4. **Backward Compatible**: Falls back to traditional chunking if no parameters specified

## Testing

Docker containers have been rebuilt and relaunched successfully:
- ✅ Backend API container rebuilt with new code
- ✅ Frontend container restarted
- ✅ All containers healthy and running
- ✅ Long text background processor initialized

## Usage

When submitting long text jobs, the advanced streaming settings (if configured) will automatically be applied:

- **Strategy**: sentence (default), paragraph, word, or fixed
- **Quality**: fast, balanced (default), or high
- **Chunk Size**: Custom size (optional, overrides quality presets)

Example: Setting "balanced quality" with "sentence strategy" will chunk long text at sentence boundaries with ~200 character target chunks, exactly like standard streaming does.
