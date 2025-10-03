# 🐳 Docker Update Status

## ✅ Dockerfiles Updated

All Dockerfiles have been updated to use **official Chatterbox TTS v0.1.4** with full 23-language support including Chinese.

### Updated Files:
- ✅ `docker/Dockerfile` - Standard version
- ✅ `docker/Dockerfile.gpu` - GPU-optimized version
- ✅ `docker/Dockerfile.cpu` - CPU-only version
- ✅ `docker/Dockerfile.uv` - UV package manager version
- ✅ `docker/Dockerfile.uv.gpu` - UV + GPU version
- ✅ `docker/Dockerfile.blackwell` - NVIDIA Blackwell (50XX) GPU version

### Changes Made:
**Before:**
```dockerfile
RUN pip install git+https://github.com/travisvn/chatterbox-multilingual.git@exp
```

**After:**
```dockerfile
RUN pip install --no-cache-dir chatterbox-tts==0.1.4
```

## 🚀 Docker Build in Progress

Building GPU-optimized container with:
- NVIDIA CUDA 12.4.1 runtime
- Official Chatterbox TTS v0.1.4
- All 23 languages including Chinese
- INT8 quantization support

### Build Command:
```bash
docker compose -f docker/docker-compose.gpu.yml up -d --build
```

## 📊 What's Included

### Model Features:
- ✅ 23 language support (including Chinese)
- ✅ Official ResembleAI model
- ✅ INT8 quantization for VRAM optimization
- ✅ GPU acceleration (CUDA 12.4)
- ✅ Voice cloning and library management

### Container Features:
- 🎯 Persistent model cache (`/cache`)
- 🎤 Persistent voice library (`/voices`)
- 📁 Persistent long text jobs (`/data/long_text_jobs`)
- 🔧 Auto health checks
- 🌐 Port 4123 exposed

## 🔍 Monitor Build Progress

```bash
# Check build logs
docker compose -f docker/docker-compose.gpu.yml logs -f

# Check container status
docker compose -f docker/docker-compose.gpu.yml ps

# Check if container is running
docker ps | grep chatterbox
```

## 🧪 Test After Launch

Once the build completes and container starts:

```bash
# Wait for model to load (first start takes ~2-5 minutes)
docker logs chatterbox-tts-api -f

# Test the API
curl http://localhost:4123/health

# Test TTS generation
curl -X POST http://localhost:4123/v1/audio/speech \
  -H "Content-Type: application/json" \
  -d '{"input": "Hello from the new official Chatterbox version!"}' \
  --output test.wav

# Test Chinese language
curl -X POST http://localhost:4123/v1/audio/speech \
  -H "Content-Type: application/json" \
  -d '{"input": "你好，今天天气真不错！"}' \
  --output chinese_test.wav
```

## 🎯 Enable INT8 Quantization

To reduce VRAM usage by 75%, add to your `.env` file:

```bash
echo "USE_INT8_QUANTIZATION=true" >> .env
docker compose -f docker/docker-compose.gpu.yml restart
```

## 📝 Environment Variables

Key variables you can customize in `.env`:

```env
# VRAM Optimization
USE_INT8_QUANTIZATION=true    # Reduces VRAM by ~75%
MODEL_DTYPE=auto              # auto/float32/float16/bfloat16

# Multilingual
USE_MULTILINGUAL_MODEL=true   # Enable all 23 languages

# Model Settings
EXAGGERATION=0.5              # Emotion intensity
CFG_WEIGHT=0.5                # Pace control
TEMPERATURE=0.8               # Randomness
```

## 🔄 Rebuild After Changes

If you modify the Dockerfile or want to use a different version:

```bash
# Stop and rebuild
docker compose -f docker/docker-compose.gpu.yml down
docker compose -f docker/docker-compose.gpu.yml up -d --build
```

## 📚 Available Compose Files

- `docker-compose.yml` - Standard (pip-based)
- `docker-compose.gpu.yml` - **GPU-optimized (currently building)**
- `docker-compose.uv.gpu.yml` - UV + GPU (faster builds)
- `docker-compose.cpu.yml` - CPU-only
- `docker-compose.blackwell.yml` - NVIDIA Blackwell GPUs

## ⏱️ Expected Build Time

- First build: 5-10 minutes (downloads base images, installs packages)
- Subsequent builds: 1-3 minutes (uses cached layers)
- First model load: 2-5 minutes (downloads model weights)

## ✅ Next Steps

1. Wait for build to complete
2. Check logs: `docker logs chatterbox-tts-api -f`
3. Test the API endpoints
4. Enable INT8 quantization if needed
5. Enjoy official 23-language support!
