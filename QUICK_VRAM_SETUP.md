# 🚀 Quick VRAM Optimization Setup

## One-Line Enable INT8 Quantization

```bash
echo "USE_INT8_QUANTIZATION=true" >> .env && uvicorn app.main:app --reload
```

## VRAM Comparison

| Setting | VRAM | Command |
|---------|------|---------|
| **INT8** (Minimal) | **0.47 GB** | `echo "USE_INT8_QUANTIZATION=true" >> .env` |
| **FP16** (Balanced) | 0.93 GB | `echo "MODEL_DTYPE=float16" >> .env` |
| **FP32** (Max Quality) | 1.86 GB | `echo "MODEL_DTYPE=float32" >> .env` |

## Test Your Setup

```bash
python tests/test_vram_optimization.py
```

## Check If Active

```bash
curl http://localhost:4123/config | jq '{quantization, dtype, device}'
```

## Full Documentation

📚 See [VRAM_OPTIMIZATION_SUMMARY.md](VRAM_OPTIMIZATION_SUMMARY.md) for complete details.
