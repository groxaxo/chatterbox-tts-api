"""
TTS model initialization and management using chatterbox-vllm backend
"""

import os
import asyncio
import torch
from enum import Enum
from typing import Optional, Dict, Any
from chatterbox_vllm.tts import ChatterboxTTS
from app.config import Config, detect_device

# Supported languages for multilingual model
# From chatterbox_vllm.text_utils
SUPPORTED_LANGUAGES = {
    "ar": "Arabic",
    "da": "Danish", 
    "de": "German",
    "el": "Greek",
    "en": "English",
    "es": "Spanish",
    "fi": "Finnish",
    "fr": "French",
    "he": "Hebrew",
    "hi": "Hindi",
    "it": "Italian",
    "ja": "Japanese",
    "ko": "Korean",
    "ms": "Malay",
    "nl": "Dutch",
    "no": "Norwegian",
    "pl": "Polish",
    "pt": "Portuguese",
    "ru": "Russian",
    "sv": "Swedish",
    "sw": "Swahili",
    "tr": "Turkish",
    "zh": "Chinese"
}

# Global model instance
_model = None
_device = None
_initialization_state = "not_started"
_initialization_error = None
_initialization_progress = ""
_is_multilingual = None
_supported_languages = {}


class InitializationState(Enum):
    NOT_STARTED = "not_started"
    INITIALIZING = "initializing"
    READY = "ready"
    ERROR = "error"


# Note: Quantization and dtype settings are not directly applicable to vLLM backend
# vLLM handles memory optimization internally through its own mechanisms


async def initialize_model():
    """Initialize the Chatterbox TTS model with vLLM backend"""
    global _model, _device, _initialization_state, _initialization_error, _initialization_progress, _is_multilingual, _supported_languages
    
    try:
        _initialization_state = InitializationState.INITIALIZING.value
        _initialization_progress = "Validating configuration..."
        
        Config.validate()
        _device = detect_device()
        
        print(f"Initializing Chatterbox TTS model with vLLM backend...")
        print(f"Device: {_device}")
        print(f"Voice sample: {Config.VOICE_SAMPLE_PATH}")
        print(f"Max batch size: {Config.VLLM_MAX_BATCH_SIZE}")
        print(f"Max model length: {Config.VLLM_MAX_MODEL_LEN}")
        
        _initialization_progress = "Creating model cache directory..."
        # Ensure model cache directory exists
        os.makedirs(Config.MODEL_CACHE_DIR, exist_ok=True)
        
        # Check voice sample exists
        if not os.path.exists(Config.VOICE_SAMPLE_PATH):
            raise FileNotFoundError(f"Voice sample not found: {Config.VOICE_SAMPLE_PATH}")
        
        # Determine if we should use multilingual model
        use_multilingual = Config.USE_MULTILINGUAL_MODEL
        
        _initialization_progress = "Loading TTS model with vLLM (this may take a while)..."
        # Initialize model with run_in_executor for non-blocking
        loop = asyncio.get_event_loop()
        
        def load_model():
            """Load the model synchronously"""
            if use_multilingual:
                print(f"Loading Chatterbox vLLM Multilingual TTS model...")
                return ChatterboxTTS.from_pretrained_multilingual(
                    max_batch_size=Config.VLLM_MAX_BATCH_SIZE,
                    max_model_len=Config.VLLM_MAX_MODEL_LEN,
                    compile=Config.VLLM_COMPILE,
                    s3gen_use_fp16=Config.VLLM_S3GEN_FP16,
                    target_device=_device
                )
            else:
                print(f"Loading standard Chatterbox vLLM TTS model...")
                return ChatterboxTTS.from_pretrained(
                    max_batch_size=Config.VLLM_MAX_BATCH_SIZE,
                    max_model_len=Config.VLLM_MAX_MODEL_LEN,
                    compile=Config.VLLM_COMPILE,
                    s3gen_use_fp16=Config.VLLM_S3GEN_FP16,
                    target_device=_device
                )
        
        _model = await loop.run_in_executor(None, load_model)
        
        # Get supported languages from the model
        _is_multilingual = use_multilingual
        _supported_languages = _model.get_supported_languages()
        
        if _is_multilingual:
            print(f"✓ Multilingual vLLM model initialized with {len(_supported_languages)} languages")
        else:
            print(f"✓ Standard vLLM model initialized (English only)")
        
        _initialization_state = InitializationState.READY.value
        _initialization_progress = "Model ready"
        _initialization_error = None
        print(f"✓ Model initialized successfully on {_device}")
        print(f"✓ vLLM backend provides ~4x speedup over standard implementation")
        return _model
        
    except Exception as e:
        _initialization_state = InitializationState.ERROR.value
        _initialization_error = str(e)
        _initialization_progress = f"Failed: {str(e)}"
        print(f"✗ Failed to initialize model: {e}")
        raise e


def get_model():
    """Get the current model instance"""
    return _model


def get_device():
    """Get the current device"""
    return _device


def get_initialization_state():
    """Get the current initialization state"""
    return _initialization_state


def get_initialization_progress():
    """Get the current initialization progress message"""
    return _initialization_progress


def get_initialization_error():
    """Get the initialization error if any"""
    return _initialization_error


def is_ready():
    """Check if the model is ready for use"""
    return _initialization_state == InitializationState.READY.value and _model is not None


def is_initializing():
    """Check if the model is currently initializing"""
    return _initialization_state == InitializationState.INITIALIZING.value 


def is_multilingual():
    """Check if the loaded model supports multilingual generation"""
    return _is_multilingual


def get_supported_languages():
    """Get the dictionary of supported languages"""
    return _supported_languages.copy()


def supports_language(language_id: str):
    """Check if the model supports a specific language"""
    return language_id in _supported_languages


def get_model_info() -> Dict[str, Any]:
    """Get comprehensive model information"""
    return {
        "backend": "vLLM",
        "model_type": "multilingual" if _is_multilingual else "standard",
        "is_multilingual": _is_multilingual,
        "supported_languages": _supported_languages,
        "language_count": len(_supported_languages),
        "device": _device,
        "is_ready": is_ready(),
        "initialization_state": _initialization_state,
        "vllm_max_batch_size": Config.VLLM_MAX_BATCH_SIZE,
        "vllm_max_model_len": Config.VLLM_MAX_MODEL_LEN,
        "vllm_compile": Config.VLLM_COMPILE,
        "vllm_diffusion_steps": Config.VLLM_DIFFUSION_STEPS
    }