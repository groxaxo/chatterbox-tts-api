# 🎨 Frontend Access Guide

## ✅ Frontend is Running!

Your Chatterbox TTS frontend is now accessible at:

### 🌐 Access URLs

- **Frontend (Web UI)**: http://localhost:4321
- **API (Direct)**: http://localhost:4123
- **API Docs**: http://localhost:4123/docs

---

## 🚀 Features Available in Frontend

### ✅ Core Features
- **Text-to-Speech Generation** - Convert text to speech with voice cloning
- **Voice Library Management** - Upload and manage custom voices
- **Language Selection** - Choose from 23 supported languages
- **Parameter Control** - Adjust temperature, CFG weight, exaggeration
- **Audio Playback** - Preview generated audio directly in browser

### ✅ Long Text Support (NEW!)
- **Automatic Chunking** - Handles texts up to 100,000 characters
- **Job Management** - Submit long text jobs for background processing
- **Progress Monitoring** - Real-time progress tracking
- **Job History** - View and manage past long text jobs
- **Download Results** - Download completed audio files

### ✅ Advanced Features
- **Streaming Support** - Real-time audio streaming
- **Voice Aliases** - Create custom voice names
- **Dark/Light Mode** - Theme switching
- **Mobile Responsive** - Works on all devices

---

## 📊 Current Status

```bash
# Check API status
curl http://localhost:4123/health

# Check available languages
curl http://localhost:4123/languages

# View API documentation
open http://localhost:4123/docs
```

### Container Status
```
✅ chatterbox-tts-api-gpu    Port 4123  (API Backend)
✅ chatterbox-tts-frontend   Port 4321  (Web Interface)
```

### Model Status
```
✅ Device: CUDA (GPU)
✅ Model: Official Chatterbox TTS v0.1.4
✅ Languages: 23 supported
✅ Status: Healthy and ready
```

---

## 🎯 Quick Start Guide

### 1. Access the Web Interface
Open your browser and go to:
```
http://localhost:4321
```

### 2. Generate Speech

**Short Text (< 3,000 characters):**
1. Enter your text in the main input area
2. Select language (optional, auto-detects)
3. Choose or upload a voice sample
4. Click "Generate Speech"
5. Audio plays automatically

**Long Text (> 3,000 characters):**
1. Enter or paste long text (up to 100,000 chars)
2. Frontend automatically detects it's long text
3. Click "Submit Long Text Job"
4. Monitor progress in real-time
5. Download when complete

### 3. Manage Voices
1. Go to "Voice Library" tab
2. Upload voice samples (WAV/MP3)
3. Name your voices
4. Use them in TTS generation

### 4. View History
1. Go to "Job History" or "Long Text History" tab
2. See all past jobs
3. Download previous results
4. Retry failed jobs

---

## 🔧 Troubleshooting

### Frontend Not Loading?
```bash
# Check containers are running
docker ps | grep chatterbox

# Check frontend logs
docker logs chatterbox-tts-frontend

# Restart if needed
docker compose -f docker/docker-compose.gpu.yml restart
```

### API Not Responding?
```bash
# Check API health
curl http://localhost:4123/health

# Check API logs
docker logs chatterbox-tts-api-gpu --tail 50

# Wait for model to load (takes ~1-2 minutes)
```

### Port Already in Use?
```bash
# Check what's using the ports
sudo lsof -i :4321  # Frontend
sudo lsof -i :4123  # API

# Stop conflicting services or change ports in docker-compose.gpu.yml
```

---

## 📚 Advanced Usage

### Process Chapter via Frontend

1. **Open Frontend**: http://localhost:4321
2. **Paste Chapter**: Copy your chapter text (e.g., from `/home/op/PrimerLibro/chapter1.txt`)
3. **Select Language**: English
4. **Choose Voice**: Use default or upload custom voice
5. **Submit**: Frontend automatically uses long text endpoint if > 3,000 chars
6. **Monitor**: Watch real-time progress
7. **Download**: Get WAV file when complete

### Use API Directly

```bash
# Short text (regular endpoint)
curl -X POST http://localhost:4123/v1/audio/speech \
  -H "Content-Type: application/json" \
  -d '{"input": "Your text here"}' \
  --output audio.wav

# Long text (background job)
curl -X POST http://localhost:4123/audio/speech/long \
  -H "Content-Type: application/json" \
  -d '{"input": "Very long text here..."}' | jq .

# Check job status
curl http://localhost:4123/audio/speech/long/{job_id} | jq .

# Download result
curl http://localhost:4123/audio/speech/long/{job_id}/download \
  --output chapter_audio.wav
```

---

## 🎨 Frontend Screenshots

The frontend includes:
- **Main TTS Interface** - Clean, modern design
- **Voice Management** - Upload and organize voices
- **Long Text Processing** - Submit and monitor jobs
- **Settings Panel** - Configure parameters
- **Dark/Light Mode** - Eye-friendly themes

---

## 🚀 Next Steps

### Process Your Book
1. Access frontend: http://localhost:4321
2. Process each chapter using long text feature
3. Download generated audio files
4. Combine into audiobook using audio editing software

### Customize Voices
1. Record 5-10 seconds of clear speech
2. Upload to Voice Library
3. Use for consistent narration
4. Create different voices for characters

### API Integration
- Integrate with your own applications
- Use OpenAI-compatible endpoints
- Build custom workflows
- Automate batch processing

---

## 📞 Support

- **Documentation**: http://localhost:4123/docs
- **GitHub**: https://github.com/groxaxo/chatterbox-tts-api
- **Original Project**: https://github.com/travisvn/chatterbox-tts-api

---

**Frontend Version**: Latest (2025 Edition)  
**Features**: All new functionality included  
**Status**: ✅ Running and ready to use
