# Long Text Audio Playback Issue Analysis

## Problem Statement

When the processing mode is set to "long text" (texts > 3000 characters), the audio does not play properly in the frontend UI. The chunks may be processed and generated on the backend, but the frontend doesn't provide a visible audio player for the final concatenated result.

## Root Cause Analysis

### Issue 1: Hidden AudioPlayer During Job Processing

**Location:** `frontend/src/pages/TTSPage.tsx:630`

```typescript
{/* Audio Player - Only show for non-streaming audio or completed streaming */}
{currentAudioUrl && !isStreaming && (
  <AudioPlayer audioUrl={currentAudioUrl} />
)}
```

**Analysis:**
- The `AudioPlayer` component only renders when `currentAudioUrl` exists AND `!isStreaming` is true
- `currentAudioUrl` is defined as: `longTextAudioUrl || streamingAudioUrl || audioUrl`
- `isStreaming` comes from `useStreamingTTS` hook (for regular streaming mode)
- This means the main AudioPlayer won't show during long text chunk streaming

### Issue 2: Chunk Playback Uses Internal Audio Element

**Location:** `frontend/src/hooks/useLongTextTTS.ts:261-287`

```typescript
// Play next chunk in queue
const playNextChunk = useCallback(() => {
  // ...
  // Create audio element
  const audio = new Audio(nextChunk.url);  // ← Internal Audio() element
  audioQueueRef.current = audio;
  
  audio.volume = 1.0;
  
  audio.onended = () => {
    console.log(`[AudioQueue] ✓ Chunk ${nextChunk.index} finished playing`);
    isPlayingRef.current = false;
    URL.revokeObjectURL(nextChunk.url);
    playNextChunk(); // Play next chunk in queue
  };
  
  audio.play().catch(err => {
    console.error(`[AudioQueue] ❌ Failed to play chunk ${nextChunk.index}. Error:`, err);
    console.error(`[AudioQueue] This might be due to browser autoplay policy.`);
    // ...
  });
}, []);
```

**Problem:**
- Chunks are played using a hidden `new Audio()` element
- **No visible audio controls** in the UI during chunk playback
- **Browser autoplay policy** may block automatic playback without user interaction
- Users can't see that audio is playing or control it

### Issue 3: Final Audio May Not Download Automatically

**Location:** `frontend/src/hooks/useLongTextTTS.ts:332-344`

```typescript
// Download completed audio
const downloadCompletedAudio = useCallback(async (jobId: string) => {
  try {
    const audioBlob = await service.downloadJobAudio(jobId);
    const audioUrl = URL.createObjectURL(audioBlob);
    setState(prev => ({ ...prev, audioUrl }));  // Sets state.audioUrl
  } catch (error) {
    console.error('Failed to download completed audio:', error);
    setState(prev => ({
      ...prev,
      error: `Failed to download audio: ${error instanceof Error ? error.message : 'Unknown error'}`
    }));
  }
}, [service]);
```

**Triggered by:** SSE 'completed' event (line 204)

```typescript
case 'completed':
case 'job_completed':
  console.log(`Long text job ${jobId} completed`);
  newState.isJobActive = false;
  newState.isStreaming = false;
  removeJobId(jobId);
  downloadCompletedAudio(jobId);  // ← Automatically downloads final audio
  break;
```

**Potential Issue:**
- If the download fails silently, no audio player will appear
- Error might be logged to console but not visible to user

### Issue 4: LongTextProgress Component Doesn't Show Audio Player

**Location:** `frontend/src/components/tts/LongTextProgress.tsx`

The `LongTextProgress` component receives `audioUrl` as a prop but I need to check if it actually displays an audio player for completed jobs.

Let me check the component further...

## Expected vs Actual Behavior

### Expected Behavior:

**During Processing:**
1. User submits text > 3000 chars
2. Job starts processing in background
3. As chunks complete:
   - Chunk audio files are generated
   - SSE sends `chunk_ready` events
   - Frontend downloads chunks
   - **Chunks play automatically in sequence** with visible progress
4. When job completes:
   - Final concatenated audio is downloaded
   - **AudioPlayer component appears** with full controls
   - User can play, pause, and download final audio

**After Completion:**
- Final audio remains accessible in the UI
- User can replay audio anytime

### Actual Behavior:

**During Processing:**
1. User submits text > 3000 chars
2. Job starts processing in background
3. As chunks complete:
   - Chunks are downloaded
   - Internal `Audio()` elements try to play
   - **No visible audio controls** for chunks
   - **Browser may block autoplay** (user sees/hears nothing)
4. When job completes:
   - Final audio is downloaded (maybe)
   - **AudioPlayer may not appear** if conditions aren't met
   - **No visible indication** that audio is ready

## The Audio Playback Flow

### Chunk-by-Chunk Playback (Progressive Streaming)

```
Backend                         Frontend
   │                               │
   │ Chunk 0 ready                 │
   ├──────(SSE)──────────────────►│ downloadCompletedAudio()
   │                               │ new Audio(chunkUrl).play()
   │                               │ [Hidden, no UI controls]
   │                               │
   │ Chunk 1 ready                 │
   ├──────(SSE)──────────────────►│ Queue chunk
   │                               │ [Waiting for chunk 0 to finish]
   │                               │
   │ Chunk 2 ready                 │
   ├──────(SSE)──────────────────►│ Queue chunk
   │                               │
   │ Job completed                 │
   ├──────(SSE)──────────────────►│ downloadCompletedAudio(jobId)
   │                               │ Download final MP3
   │                               │ setState({ audioUrl })
   │                               │
   │                               │ SHOULD show AudioPlayer
   │                               │ but may not appear...
```

### Browser Autoplay Policy

Modern browsers (Chrome, Firefox, Safari) block automatic audio playback unless:
1. User has interacted with the page (clicked something)
2. Audio is muted
3. Site has high media engagement score

**Impact on Long Text Mode:**
```typescript
audio.play().catch(err => {
  console.error(`[AudioQueue] ❌ Failed to play chunk ${nextChunk.index}. Error:`, err);
  console.error(`[AudioQueue] This might be due to browser autoplay policy. User interaction required.`);
  // Audio fails silently - user sees/hears nothing!
});
```

## Why Users See No Audio Playback

### Scenario 1: Chunks Play But User Doesn't Know

- Chunks download and queue successfully
- Browser blocks `audio.play()` due to autoplay policy
- No error shown in UI
- User thinks nothing is happening
- **Solution:** Show visible audio controls or play button

### Scenario 2: Final Audio Doesn't Appear

- Job completes
- `downloadCompletedAudio()` is called
- Audio download succeeds, `longTextAudioUrl` is set
- But `AudioPlayer` component doesn't render because:
  - Some other condition prevents rendering
  - `currentAudioUrl` is falsy
  - Component is conditionally hidden
- **Solution:** Check rendering conditions

### Scenario 3: Download Fails Silently

- Job completes
- `downloadCompletedAudio()` tries to fetch final audio
- Network error or backend issue
- Error logged to console but not shown to user
- **Solution:** Show error UI

## Debugging Steps

### Check Browser Console

When testing long text mode, look for these log messages:

**Expected Success Messages:**
```
[Long Text TTS] Received SSE event for job ...: chunk_ready
[Chunk Download] ⬇️  Downloading chunk 0 from /audio/speech/long/.../chunks/0
[Chunk Download] ✅ Chunk 0 downloaded (0.5MB), adding to queue
[AudioQueue] 🔊 Playing chunk 0, queue remaining: 0
[AudioQueue] ✓ Chunk 0 finished playing
```

**Autoplay Blocked Messages:**
```
[AudioQueue] ❌ Failed to play chunk 0. Error: DOMException: play() failed...
[AudioQueue] This might be due to browser autoplay policy. User interaction required.
```

**Download Errors:**
```
Failed to download completed audio: Error: ...
```

### Check Network Tab

1. Open DevTools → Network tab
2. Filter by "long" or "chunks"
3. Look for requests to:
   - `GET /audio/speech/long/{job_id}/chunks/0` (should return 200 OK with audio/wav)
   - `GET /audio/speech/long/{job_id}/chunks/1`
   - `GET /audio/speech/long/{job_id}/download` (should return 200 OK with audio/mp3)

### Check Application State

Add `console.log` in TTSPage.tsx:

```typescript
// Line 398
const currentAudioUrl = longTextAudioUrl || streamingAudioUrl || audioUrl;
console.log('[DEBUG] Audio URLs:', {
  longTextAudioUrl,
  streamingAudioUrl,
  audioUrl,
  currentAudioUrl,
  isStreaming
});
```

Should show:
- `longTextAudioUrl`: blob URL after job completes
- `isStreaming`: false (from useStreamingTTS, not long text)
- `currentAudioUrl`: should equal longTextAudioUrl

## Solutions

### Solution 1: Add Visible Audio Controls to LongTextProgress (Quick Fix)

**File:** `frontend/src/components/tts/LongTextProgress.tsx`

Currently, this component shows job progress but might not show audio controls during chunk playback. Add an audio player for the chunks or final audio.

### Solution 2: User-Initiated Playback (Recommended)

Instead of auto-playing chunks, show a "Play" button that user clicks to start playback. This bypasses browser autoplay restrictions.

**Implementation:**
```typescript
// In useLongTextTTS.ts
const [userInitiatedPlayback, setUserInitiatedPlayback] = useState(false);

// In LongTextProgress component
{isJobActive && chunks.length > 0 && (
  <Button onClick={() => {
    setUserInitiatedPlayback(true);
    playNextChunk();
  }}>
    ▶️ Start Playback
  </Button>
)}
```

### Solution 3: Always Show AudioPlayer for Completed Jobs

**File:** `frontend/src/pages/TTSPage.tsx:630`

```typescript
{/* CURRENT - May hide during long text processing */}
{currentAudioUrl && !isStreaming && (
  <AudioPlayer audioUrl={currentAudioUrl} />
)}

{/* PROPOSED - Always show when audio is available */}
{(currentAudioUrl || longTextAudioUrl) && (
  <AudioPlayer audioUrl={currentAudioUrl || longTextAudioUrl} />
)}
```

### Solution 4: Better Error Handling

**File:** `frontend/src/hooks/useLongTextTTS.ts:332-344`

```typescript
const downloadCompletedAudio = useCallback(async (jobId: string) => {
  try {
    console.log(`[Long Text] Downloading final audio for job ${jobId}...`);
    const audioBlob = await service.downloadJobAudio(jobId);
    const audioUrl = URL.createObjectURL(audioBlob);
    
    console.log(`[Long Text] ✅ Final audio downloaded:`, {
      size: audioBlob.size,
      type: audioBlob.type,
      url: audioUrl
    });
    
    setState(prev => ({ ...prev, audioUrl }));
  } catch (error) {
    console.error('[Long Text] ❌ Failed to download completed audio:', error);
    
    // Show user-visible error
    setState(prev => ({
      ...prev,
      error: `Failed to download audio: ${error instanceof Error ? error.message : 'Unknown error'}. Please try downloading from the job list.`
    }));
    
    // Could also show a toast notification here
  }
}, [service]);
```

### Solution 5: Check LongTextProgress Audio Display

The `LongTextProgress` component receives `audioUrl` but may not display it properly. Let me check if it has an audio player or download button...

## Recommendations

1. **Immediate:** Add console logging to verify audio download succeeds
2. **Quick Fix:** Add visible audio controls or play button to LongTextProgress
3. **Medium-term:** Implement user-initiated playback to avoid autoplay issues
4. **Long-term:** Redesign chunk playback UI to show progress and controls

## Testing Checklist

- [ ] Test with text > 3000 characters
- [ ] Open browser console and check for errors
- [ ] Verify chunks download successfully (Network tab)
- [ ] Check if autoplay is blocked (console messages)
- [ ] Verify final audio downloads after job completes
- [ ] Check if AudioPlayer component renders
- [ ] Test on different browsers (Chrome, Firefox, Safari)
- [ ] Test with and without prior user interaction

---

**Next Steps:** Check `LongTextProgress.tsx` to see if it has audio playback functionality, then implement appropriate fixes.
