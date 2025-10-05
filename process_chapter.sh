#!/bin/bash
# Process chapter1.txt with TTS and monitor performance

CHAPTER_FILE="/home/op/PrimerLibro/chapter1.txt"
OUTPUT_FILE="/tmp/chapter1_audio.wav"
LOG_FILE="/tmp/tts_performance.log"

echo "=== Processing Chapter 1 with TTS ===" | tee $LOG_FILE
echo "File: $CHAPTER_FILE" | tee -a $LOG_FILE
echo "Size: $(wc -c < $CHAPTER_FILE) characters" | tee -a $LOG_FILE
echo "" | tee -a $LOG_FILE

# Start GPU monitoring in background
echo "Starting GPU monitoring..." | tee -a $LOG_FILE
nvidia-smi dmon -s u -c 30 > /tmp/gpu_usage.log 2>&1 &
GPU_MON_PID=$!

# Get initial stats
echo "=== Initial State ===" | tee -a $LOG_FILE
echo "GPU Memory:" | tee -a $LOG_FILE
nvidia-smi --query-gpu=index,memory.used,memory.total --format=csv,noheader | tee -a $LOG_FILE
echo "" | tee -a $LOG_FILE

# Read the chapter text (first 2900 chars to fit limit)
CHAPTER_TEXT=$(cat $CHAPTER_FILE | head -c 2900)

# Start timing
START_TIME=$(date +%s)

echo "=== Starting TTS Generation ===" | tee -a $LOG_FILE
echo "Start time: $(date)" | tee -a $LOG_FILE

# Process with TTS API
curl -X POST http://localhost:4123/v1/audio/speech \
  -H "Content-Type: application/json" \
  -d "{\"input\":$(echo "$CHAPTER_TEXT" | jq -Rs .)}" \
  --output $OUTPUT_FILE \
  -w "\nHTTP Code: %{http_code}\nTime: %{time_total}s\n" 2>&1 | tee -a $LOG_FILE

# End timing
END_TIME=$(date +%s)
DURATION=$((END_TIME - START_TIME))

# Stop GPU monitoring
kill $GPU_MON_PID 2>/dev/null

echo "" | tee -a $LOG_FILE
echo "=== Generation Complete ===" | tee -a $LOG_FILE
echo "End time: $(date)" | tee -a $LOG_FILE
echo "Total duration: ${DURATION} seconds" | tee -a $LOG_FILE
echo "Output file: $OUTPUT_FILE" | tee -a $LOG_FILE
echo "File size: $(ls -lh $OUTPUT_FILE | awk '{print $5}')" | tee -a $LOG_FILE
echo "" | tee -a $LOG_FILE

# Show final GPU stats
echo "=== Final GPU State ===" | tee -a $LOG_FILE
nvidia-smi --query-gpu=index,memory.used,utilization.gpu --format=csv,noheader | tee -a $LOG_FILE
echo "" | tee -a $LOG_FILE

# Show GPU usage summary
echo "=== GPU Utilization During Generation ===" | tee -a $LOG_FILE
if [ -f /tmp/gpu_usage.log ]; then
    echo "Average GPU utilization:" | tee -a $LOG_FILE
    awk 'NR>2 {sum+=$2; count++} END {if(count>0) print "  GPU: " sum/count "%"}' /tmp/gpu_usage.log | tee -a $LOG_FILE
fi

echo "" | tee -a $LOG_FILE
echo "Full performance log saved to: $LOG_FILE"
echo "GPU monitoring log saved to: /tmp/gpu_usage.log"
echo ""
echo "✅ Chapter 1 audio generated successfully!"
echo "   Play with: ffplay $OUTPUT_FILE"
