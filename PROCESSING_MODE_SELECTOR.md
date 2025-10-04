# Processing Mode Selector - Manual Mode Selection

## Overview

Added a manual processing mode selector that gives users full control over whether to use **Streaming** or **Long Text** processing, instead of relying solely on automatic detection based on text length.

## Problem Solved

Previously, the system automatically chose between streaming and long text modes based on a 3000-character threshold. This automatic detection wasn't always working properly and didn't give users control over the processing method.

## Solution Implemented

### New UI Component: **Processing Mode Selector**

A new selector card appears in the UI with three options:

#### 1. **Auto Mode (Recommended)** 🪄
- Automatically chooses based on text length
- Text > 3000 characters → Long Text mode
- Text ≤ 3000 characters → Streaming mode
- **Default setting**

#### 2. **Streaming Mode** ⚡
- Forces streaming for ANY text length
- Real-time audio generation
- Best for shorter texts
- Use when you want immediate streaming regardless of length

#### 3. **Long Text Mode** 📚
- Forces background processing for ANY text length
- Background job with progress tracking
- Best for longer texts
- Use when you want job-based processing regardless of length

## Features

### Visual Feedback
- Shows current selection with highlighted border
- Displays "Auto → Streaming" or "Auto → Long Text" when in auto mode
- Real-time text length display
- Animated indicator on selected mode
- Recommended badge on Auto mode

### Persistent Settings
- Selection is saved to localStorage
- Persists across browser sessions
- Each user's preference is remembered

### Verbose Logging
- Logs mode selection changes
- Logs processing decisions in console
- Shows exact reasoning for mode choice
- Helps with debugging

## Technical Implementation

### New Files Created

1. **`frontend/src/hooks/useProcessingMode.ts`**
   - React hook for managing processing mode state
   - Handles localStorage persistence
   - Provides `shouldUseLongText()` function that respects manual overrides

2. **`frontend/src/components/tts/ProcessingModeSelector.tsx`**
   - UI component for mode selection
   - Card-based interface with three options
   - Shows contextual information based on text length

### Modified Files

1. **`frontend/src/pages/TTSPage.tsx`**
   - Integrated `useProcessingMode` hook
   - Replaced automatic detection with manual mode-aware logic
   - Added ProcessingModeSelector component to UI

2. **`frontend/src/components/tts/index.ts`**
   - Exported ProcessingModeSelector for easy imports

## Usage

### For Users

1. **Open the TTS interface**
2. **Look for "Processing Mode" card** (appears below voice selection)
3. **Choose your preferred mode:**
   - Leave on **Auto** (recommended) for automatic selection
   - Select **Streaming** to force real-time streaming
   - Select **Long Text** to force background processing

4. The system will respect your choice regardless of text length

### For Developers

```typescript
// Import the hook
import { useProcessingMode } from '../hooks/useProcessingMode';

// Use in component
const { 
  mode,                      // Current mode: 'auto' | 'streaming' | 'long-text'
  setMode,                   // Change mode
  shouldUseLongText,         // Check if long text should be used
  isAuto,                    // Boolean: is auto mode?
  isManualStreaming,         // Boolean: manually set to streaming?
  isManualLongText          // Boolean: manually set to long-text?
} = useProcessingMode();

// Check processing decision
const useLongText = shouldUseLongText(text);

// Manual override
setMode('streaming');  // Force streaming mode
setMode('long-text');  // Force long text mode
setMode('auto');       // Back to automatic
```

## Console Logging

When processing decisions are made, you'll see logs like:

```
[ProcessingMode] Setting mode to: streaming
[ProcessingMode] Saved to localStorage: {mode: "streaming"}
[ProcessingMode] shouldUseLongText check: {mode: "streaming", textLength: 5000, threshold: 3000}
[ProcessingMode] Using STREAMING mode (manual override)
[TTSPage] Processing mode decision: {mode: "streaming", textLength: 5000, useLongTextMode: false}
```

## Benefits

✅ **User Control**: Users can override automatic detection  
✅ **Better UX**: Clear visual feedback on what mode will be used  
✅ **Debugging**: Verbose logging shows exactly what's happening  
✅ **Persistent**: User preference saved across sessions  
✅ **Flexible**: Works with any text length  
✅ **Safe**: Auto mode still available as default (recommended)  

## Testing

### Test Case 1: Auto Mode
1. Set mode to "Auto"
2. Enter text < 3000 characters
3. Generate → Should use streaming
4. Enter text > 3000 characters
5. Generate → Should use long text

### Test Case 2: Manual Streaming
1. Set mode to "Streaming"
2. Enter text > 3000 characters (normally would be long text)
3. Generate → Should use streaming anyway

### Test Case 3: Manual Long Text
1. Set mode to "Long Text"
2. Enter text < 3000 characters (normally would be streaming)
3. Generate → Should use long text anyway

### Test Case 4: Persistence
1. Set mode to "Streaming"
2. Refresh the page
3. Check mode → Should still be "Streaming"

## Location in UI

The **Processing Mode Selector** appears:
- Below the voice selection/voice library
- Above the Advanced Settings section
- In the main TTS generation flow

This placement ensures users see it before configuring other settings or generating audio.

## Default Behavior

- **Default mode**: Auto (recommended)
- **No breaking changes**: Existing behavior preserved in auto mode
- **Opt-in manual control**: Users must explicitly choose streaming/long-text to override

## Future Enhancements

Potential improvements:
- Save mode per voice (different voices might work better with different modes)
- Add "Smart" mode that considers other factors beyond text length
- Show estimated processing time for each mode
- Add tooltips explaining when to use each mode
- Mode recommendations based on text characteristics (not just length)
