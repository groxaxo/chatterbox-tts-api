# 🎉 Update to Official Chatterbox TTS v0.1.4

## What Changed

### ✅ Updated to Official Version
- **Before**: Using experimental fork `travisvn/chatterbox-multilingual@exp`
- **After**: Using official **`chatterbox-tts==0.1.4`** from ResembleAI

### 🌍 Full Language Support (23 Languages)
- **Added**: Chinese (zh) language support
- **Total**: Now supports all **23 languages** officially

### 📝 Updated Files

1. **`requirements.txt`**
   - Changed from experimental fork to official version
   - Now uses: `chatterbox-tts==0.1.4`

2. **`app/core/mtl.py`**
   - Added Chinese (zh) to SUPPORTED_LANGUAGES
   - Updated comments to reflect official support

3. **`README.md`**
   - Updated "22 languages" → "23 languages"
   - Added Chinese to supported languages list
   - Updated NOTE section to reflect official version
   - Renamed "Issues with Multilingual?" → "Multilingual Model Information"
   - Updated installation instructions

## Supported Languages (23)

Arabic (ar) • Danish (da) • German (de) • Greek (el) • **English (en)** • Spanish (es) • Finnish (fi) • French (fr) • Hebrew (he) • Hindi (hi) • Italian (it) • Japanese (ja) • Korean (ko) • Malay (ms) • Dutch (nl) • Norwegian (no) • Polish (pl) • Portuguese (pt) • Russian (ru) • Swedish (sv) • Swahili (sw) • Turkish (tr) • **Chinese (zh)**

## How to Apply

```bash
# Reinstall with official version
pip install -r requirements.txt --upgrade

# Restart the API
uvicorn app.main:app --host 0.0.0.0 --port 4123
```

## Test Chinese Support

```bash
curl -X POST http://localhost:4123/v1/audio/speech \
  -H "Content-Type: application/json" \
  -d '{"input": "你好，今天天气真不错，希望你有一个愉快的周末。", "voice": "default"}' \
  --output chinese_test.wav
```

## VRAM Optimization Still Available

INT8 quantization is still fully functional:

```bash
echo "USE_INT8_QUANTIZATION=true" >> .env
```

This reduces VRAM from ~1.86GB to **~0.47GB** (75% savings)!

## What's Next

1. ✅ Install the updated requirements
2. ✅ Test the API with different languages
3. ✅ Enable INT8 quantization if you need VRAM savings
4. ✅ Enjoy official multilingual support!
