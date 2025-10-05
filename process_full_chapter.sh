#!/bin/bash
# Process full chapter using Long Text TTS API

CHAPTER_FILE="/home/op/PrimerLibro/chapter1.txt"
CHAPTER_TEXT=$(cat "$CHAPTER_FILE")
CHAR_COUNT=$(echo -n "$CHAPTER_TEXT" | wc -c)

echo "=== Long Text TTS Processing ==="
echo "File: $CHAPTER_FILE"
echo "Characters: $CHAR_COUNT"
echo ""

# Check if we should use long text endpoint
if [ $CHAR_COUNT -gt 3000 ]; then
    echo "✅ Using LONG TEXT endpoint (supports up to 100,000 chars)"
    echo "   Text will be automatically split into chunks"
    echo "   Chunks will be processed and concatenated"
    echo ""
    
    # Submit job
    echo "📤 Submitting long text job..."
    RESPONSE=$(curl -s -X POST http://localhost:4123/audio/speech/long \
      -H "Content-Type: application/json" \
      -d "{\"input\":$(echo "$CHAPTER_TEXT" | jq -Rs .)}")
    
    JOB_ID=$(echo "$RESPONSE" | jq -r '.job_id')
    
    if [ "$JOB_ID" = "null" ] || [ -z "$JOB_ID" ]; then
        echo "❌ Error submitting job:"
        echo "$RESPONSE" | jq .
        exit 1
    fi
    
    echo "✅ Job submitted successfully!"
    echo "   Job ID: $JOB_ID"
    echo ""
    
    # Monitor progress
    echo "📊 Monitoring progress..."
    echo ""
    
    while true; do
        STATUS=$(curl -s "http://localhost:4123/audio/speech/long/$JOB_ID")
        STATE=$(echo "$STATUS" | jq -r '.status')
        PROGRESS=$(echo "$STATUS" | jq -r '.progress')
        CURRENT=$(echo "$STATUS" | jq -r '.current_chunk')
        TOTAL=$(echo "$STATUS" | jq -r '.total_chunks')
        
        echo -ne "\r⏳ Status: $STATE | Progress: $PROGRESS% | Chunk: $CURRENT/$TOTAL     "
        
        if [ "$STATE" = "completed" ]; then
            echo ""
            echo ""
            echo "✅ Job completed!"
            
            # Download the audio
            OUTPUT_FILE="/tmp/chapter1_full_audio.wav"
            echo "📥 Downloading audio..."
            curl -s "http://localhost:4123/audio/speech/long/$JOB_ID/download" \
                --output "$OUTPUT_FILE"
            
            echo "✅ Audio saved to: $OUTPUT_FILE"
            echo "   Size: $(ls -lh $OUTPUT_FILE | awk '{print $5}')"
            echo ""
            echo "🎵 Play with: ffplay $OUTPUT_FILE"
            break
        elif [ "$STATE" = "failed" ]; then
            echo ""
            echo "❌ Job failed!"
            echo "$STATUS" | jq .
            exit 1
        fi
        
        sleep 2
    done
else
    echo "ℹ️  Text is short enough for regular endpoint"
    echo "   Use: curl -X POST http://localhost:4123/v1/audio/speech"
fi
