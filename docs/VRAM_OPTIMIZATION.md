# VRAM Optimization Guide

This guide explains how to optimize VRAM usage for the Chatterbox TTS API through quantization and precision control.

## 📊 VRAM Usage Overview

The Chatterbox TTS model (~500M parameters) uses different amounts of VRAM depending on precision:

| Precision | VRAM Usage | Savings vs FP32 | Savings vs FP16 |
|-----------|------------|-----------------|-----------------|
| **FP32** (Float32) | ~1.86 GB | - | - |
| **FP16** (Float16) | ~0.93 GB | 50% (0.93 GB saved) | - |
| **INT8** (Quantized) | ~0.47 GB | 75% (1.40 GB saved) | 50% (0.47 GB saved) |

## 🚀 Quick Start - Enable INT8 Quantization

The easiest way to reduce VRAM usage is to enable INT8 quantization:

```bash
# Edit your .env file
echo "USE_INT8_QUANTIZATION=true" >> .env

# Restart the API
uvicorn app.main:app --host 0.0.0.0 --port 4123
```

**Benefits:**
- ✅ ~50% VRAM reduction (compared to FP16)
- ✅ ~75% VRAM reduction (compared to FP32)
- ✅ Faster inference on some hardware
- ✅ Minimal quality impact for most use cases

**Trade-offs:**
- ⚠️ Slight quality degradation (usually imperceptible)
- ⚠️ Not compatible with all model operations

## ⚙️ Configuration Options

### 1. INT8 Quantization (Recommended for Low VRAM)

```env
# Enable INT8 quantization
USE_INT8_QUANTIZATION=true
```

This applies dynamic quantization to Linear, LSTM, and GRU layers, reducing memory footprint significantly.

### 2. Data Type Selection

```env
# Choose model precision
MODEL_DTYPE=auto  # Options: auto, float32, float16, bfloat16
```

**Options:**
- `auto` - Automatically selects optimal dtype:
  - CUDA: float16 (recommended)
  - MPS (Mac): float32
  - CPU: float32
  
- `float16` - Half precision (50% VRAM vs float32)
  - Best for CUDA GPUs
  - Good balance of quality and performance
  
- `bfloat16` - Brain Float16
  - Better numerical stability than float16
  - Requires compatible hardware (newer GPUs/CPUs)
  
- `float32` - Full precision
  - Highest quality
  - Highest VRAM usage

### 3. Combined Optimization

You can combine dtype selection with quantization, but **INT8 quantization takes precedence**:

```env
# This will use INT8 quantization (MODEL_DTYPE is ignored when quantization is enabled)
USE_INT8_QUANTIZATION=true
MODEL_DTYPE=float16
```

## 📈 Optimization Strategies

### Strategy 1: Maximum Quality (High VRAM)
```env
USE_INT8_QUANTIZATION=false
MODEL_DTYPE=float32
```
- VRAM: ~1.86 GB
- Use case: High-end GPUs, maximum quality needed

### Strategy 2: Balanced (Recommended)
```env
USE_INT8_QUANTIZATION=false
MODEL_DTYPE=auto  # Uses float16 on CUDA
```
- VRAM: ~0.93 GB (CUDA) or ~1.86 GB (CPU/MPS)
- Use case: Most production deployments

### Strategy 3: Minimum VRAM (Best for Limited Resources)
```env
USE_INT8_QUANTIZATION=true
MODEL_DTYPE=auto  # Ignored when quantization is enabled
```
- VRAM: ~0.47 GB
- Use case: Limited VRAM, multiple models, or batch processing

## 🔍 Monitoring VRAM Usage

The API provides endpoints to monitor VRAM usage:

```bash
# Check model information (includes quantization status)
curl http://localhost:4123/config

# Monitor memory usage
curl http://localhost:4123/memory

# Get detailed model info
curl http://localhost:4123/info
```

**Response includes:**
```json
{
  "quantization": "int8",  // or "none"
  "dtype": "auto",
  "device": "cuda",
  // ... other info
}
```

## 🧪 Testing Quantization

Test the quality impact of quantization:

1. **Generate with full precision:**
```bash
# Disable quantization
USE_INT8_QUANTIZATION=false

curl -X POST http://localhost:4123/v1/audio/speech \
  -H "Content-Type: application/json" \
  -d '{"input": "Test speech quality"}' \
  --output test_fp16.wav
```

2. **Generate with INT8 quantization:**
```bash
# Enable quantization
USE_INT8_QUANTIZATION=true

curl -X POST http://localhost:4123/v1/audio/speech \
  -H "Content-Type: application/json" \
  -d '{"input": "Test speech quality"}' \
  --output test_int8.wav
```

3. **Compare the audio files** to determine if the quality trade-off is acceptable for your use case.

## 🐳 Docker Deployment

For Docker deployments, update your environment file:

```bash
# Copy Docker-specific env file
cp .env.example.docker .env

# Enable quantization
echo "USE_INT8_QUANTIZATION=true" >> .env

# Start with GPU support
docker compose -f docker/docker-compose.gpu.yml up -d
```

## ⚡ Performance Tips

1. **CUDA GPUs**: Use `MODEL_DTYPE=float16` for best performance without quantization
2. **Limited VRAM**: Enable `USE_INT8_QUANTIZATION=true`
3. **CPU Inference**: Keep `MODEL_DTYPE=float32` (quantization can still help)
4. **Apple Silicon (MPS)**: Use `MODEL_DTYPE=float32` for stability

## 🐛 Troubleshooting

### Model fails to load with quantization

**Error:** Model quantization fails or produces errors

**Solution:**
```env
# Disable quantization and use float16 instead
USE_INT8_QUANTIZATION=false
MODEL_DTYPE=float16
```

### Out of memory errors

**Error:** CUDA out of memory or similar

**Solutions:**
1. Enable INT8 quantization:
   ```env
   USE_INT8_QUANTIZATION=true
   ```

2. Reduce chunk size:
   ```env
   MAX_CHUNK_LENGTH=200
   ```

3. Increase memory cleanup frequency:
   ```env
   MEMORY_CLEANUP_INTERVAL=3
   CUDA_CACHE_CLEAR_INTERVAL=2
   ```

### Quality degradation with INT8

If INT8 quantization produces unacceptable quality:

1. Try float16 instead:
   ```env
   USE_INT8_QUANTIZATION=false
   MODEL_DTYPE=float16
   ```

2. Use bfloat16 if supported:
   ```env
   USE_INT8_QUANTIZATION=false
   MODEL_DTYPE=bfloat16
   ```

## 📚 Additional Resources

- [Memory Management Documentation](MEMORY_MANAGEMENT.md)
- [Performance Tuning Guide](PERFORMANCE.md)
- [Docker Deployment](DOCKER_README.md)

## 💡 Best Practices

1. **Test First**: Always test quantization impact on your specific use case
2. **Monitor Memory**: Use the `/memory` endpoint to track actual VRAM usage
3. **Start Conservative**: Begin with `MODEL_DTYPE=auto`, then try quantization
4. **Production**: Consider `float16` as a good middle ground for CUDA deployments
5. **Development**: Use `float32` for maximum quality during testing

## 🔬 Technical Details

### INT8 Dynamic Quantization

The implementation uses PyTorch's `quantize_dynamic()` which:
- Quantizes weights to INT8 at load time
- Uses INT8 arithmetic during computation
- Dynamically quantizes activations during inference
- Targets Linear, LSTM, and GRU layers (most memory-intensive)

### Data Type Precision

- **Float32 (FP32)**: 32-bit floating point, full precision
- **Float16 (FP16)**: 16-bit floating point, half precision
- **BFloat16 (BF16)**: 16-bit brain float, better range than FP16
- **INT8**: 8-bit integer quantization, smallest footprint

The choice depends on your hardware capabilities and quality requirements.
