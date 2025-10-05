#!/bin/bash
# GPU Usage Monitor for Chatterbox TTS

echo "=== GPU vs CPU Usage Monitor ==="
echo "Press Ctrl+C to stop"
echo ""

while true; do
    clear
    echo "=== CURRENT GPU STATUS ==="
    nvidia-smi --query-gpu=index,name,temperature.gpu,utilization.gpu,utilization.memory,memory.used,memory.total --format=csv,noheader,nounits | head -1
    
    echo ""
    echo "=== DOCKER CONTAINER STATS ==="
    docker stats chatterbox-tts-api-gpu --no-stream --format "CPU: {{.CPUPerc}}\tRAM: {{.MemUsage}}"
    
    echo ""
    echo "=== EXPLANATION ==="
    echo "✅ Model runs on GPU (see GPU memory: ~3.8GB used)"
    echo "✅ CPU usage is minimal (should be <5% when idle)"
    echo "📊 During TTS generation:"
    echo "   - Text preprocessing: CPU (fast)"
    echo "   - Neural network: GPU ← THIS IS THE HEAVY WORK"
    echo "   - Audio encoding: CPU (fast)"
    echo ""
    echo "Updating in 2 seconds..."
    sleep 2
done
